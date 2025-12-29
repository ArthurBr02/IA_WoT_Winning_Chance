from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import asyncio
import hashlib
from pathlib import Path
import logging

import httpx
from fastapi import Body, FastAPI, HTTPException, Query
from pydantic import AliasChoices, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Pydantic v2: éviter le warning de conflit avec le namespace protégé `model_`
        protected_namespaces=("settings_",),
    )

    api_title: str = "API"
    api_prefix: str = "/api"
    route_health: str = "/health"

    http_timeout_seconds: float = 20

    # --- Wargaming proxy (dedicated routes)
    wargaming_region: str = "eu"  # eu|na|ru|asia
    # application_id (WG). Historically called WARGAMING_API_KEY in this project.
    wargaming_app_id: str = Field(default="", validation_alias=AliasChoices("WARGAMING_APP_ID", "WARGAMING_API_KEY"))

    # --- Tomato proxy (dedicated routes)
    tomato_api_base_url: str = "https://api.tomato.gg/api"

    # --- ML artifacts (trained in ../ml)
    model_path: str = Field(default="", validation_alias=AliasChoices("MODEL_PATH"))
    scaler_path: str = Field(default="", validation_alias=AliasChoices("SCALER_PATH"))
    map_index_path: str = Field(default="", validation_alias=AliasChoices("MAP_INDEX_PATH"))


settings = Settings()

logger = logging.getLogger("api")

app = FastAPI(title=settings.api_title)


WG_BASE_URLS: Dict[str, str] = {
    "eu": "https://api.worldoftanks.eu/wot",
    "na": "https://api.worldoftanks.com/wot",
    "ru": "https://api.worldoftanks.ru/wot",
    "asia": "https://api.worldoftanks.asia/wot",
}
class HttpRequest(BaseModel):
    pass


class PredictWinRequest(BaseModel):
    # Utilisateur courant + son spawn (requis)
    user: str = Field(
        ..., description="Pseudo de l'utilisateur courant", validation_alias=AliasChoices("user", "current_user", "nickname")
    )
    user_spawn: int = Field(
        ...,
        ge=1,
        le=2,
        description="Spawn/équipe de l'utilisateur courant: 1 ou 2",
        validation_alias=AliasChoices("user_spawn", "current_user_spawn", "spawn"),
    )

    # Liste complète (optionnelle si spawn_1/spawn_2 ou players est fourni)
    pseudos: Optional[List[str]] = Field(default=None, description="Liste de pseudos (optionnel)")

    # Requis pour le modèle "WithMap" (cf ml/main.py)
    map_id: Optional[int] = Field(default=None, description="ID numérique de la map (colonne 'map' dans les CSV)")

    # Option 1: fournir explicitement les équipes
    spawn_1: Optional[List[str]] = Field(default=None, description="Liste des pseudos équipe spawn_1 (max 15)")
    spawn_2: Optional[List[str]] = Field(default=None, description="Liste des pseudos équipe spawn_2 (max 15)")


class PlayerWithSpawn(BaseModel):
    name: str
    spawn: int = Field(ge=1, le=2)


class PredictWinRequestWithPlayers(PredictWinRequest):
    # Option 2: fournir tous les joueurs avec leur spawn
    players: Optional[List[PlayerWithSpawn]] = None


class PredictFeaturesResponse(BaseModel):
    user: str
    user_spawn: int
    region: str
    map_id: Optional[int] = None
    map_index: Optional[int] = None
    map_unknown: bool = False
    players: Dict[str, Dict[str, Any]]
    missing_players: Dict[str, str] = Field(default_factory=dict)


FEATURE_COLS: Tuple[str, ...] = (
    "battles",
    "overallWN8",
    "overallWNX",
    "winrate",
    "dpg",
    "assist",
    "frags",
    "survival",
    "spots",
    "cap",
    "def",
    "xp",
    "kd",
)
MAX_PLAYERS: int = 15
MAP_EMBEDDING_DIM: int = 10


def _normalize_pseudos(pseudos: List[str]) -> List[str]:
    cleaned: List[str] = []
    for pseudo in pseudos:
        if pseudo is None:
            continue
        p = str(pseudo).strip()
        if not p:
            continue
        cleaned.append(p)
    return cleaned


def _parse_csv_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return _normalize_pseudos([v.strip() for v in value.split(",")])


def _split_teams_from_request(payload: PredictWinRequest) -> Tuple[List[str], List[str]]:
    # Priorité 1: équipes explicites
    if payload.spawn_1 is not None or payload.spawn_2 is not None:
        team1 = _normalize_pseudos(payload.spawn_1 or [])
        team2 = _normalize_pseudos(payload.spawn_2 or [])
        return team1[:MAX_PLAYERS], team2[:MAX_PLAYERS]

    # Priorité 2: players[] avec spawn
    players = getattr(payload, "players", None)
    if players:
        team1 = []
        team2 = []
        for p in players:
            try:
                name = str(getattr(p, "name", "")).strip()
                sp = int(getattr(p, "spawn", 0))
            except Exception:
                continue
            if not name:
                continue
            if sp == 1:
                team1.append(name)
            elif sp == 2:
                team2.append(name)
        return _normalize_pseudos(team1)[:MAX_PLAYERS], _normalize_pseudos(team2)[:MAX_PLAYERS]

    # Fallback simple: on prend les 15 premiers comme spawn_1 et les 15 suivants comme spawn_2
    pseudos = _normalize_pseudos(payload.pseudos or [])
    return pseudos[:MAX_PLAYERS], pseudos[MAX_PLAYERS : MAX_PLAYERS * 2]


def _safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def _get_padded_team_vector(team_stats: List[Dict[str, Any]]) -> List[float]:
    # Tri desc sur overallWN8 (comme ml/main.py)
    sorted_team = sorted(team_stats, key=lambda d: _safe_float(d.get("overallWN8")), reverse=True)

    rows: List[List[float]] = []
    for p in sorted_team[:MAX_PLAYERS]:
        rows.append([_safe_float(p.get(col)) for col in FEATURE_COLS])

    while len(rows) < MAX_PLAYERS:
        rows.append([0.0] * len(FEATURE_COLS))

    flat: List[float] = []
    for r in rows:
        flat.extend(r)
    return flat


def _resolve_artifact_path(*candidates: str) -> Path:
    base_dir = Path(__file__).resolve().parent
    for cand in candidates:
        if not cand:
            continue
        p = Path(cand)
        if not p.is_absolute():
            p = (base_dir / p).resolve()
        if p.exists():
            return p
    raise FileNotFoundError("No valid artifact path found among candidates")


class _Artifacts:
    def __init__(self, model: Any, scaler: Any, map_index: Dict[int, int]):
        self.model = model
        self.scaler = scaler
        self.map_index = map_index


_ARTIFACTS: Optional[_Artifacts] = None
_ARTIFACTS_LOCK = asyncio.Lock()


def _make_model(num_maps: int, stats_input_size: int):
    import torch
    import torch.nn as nn

    class WinPredictorWithMap(nn.Module):
        def __init__(self, num_maps: int, stats_input_size: int):
            super(WinPredictorWithMap, self).__init__()
            self.map_embedding = nn.Embedding(num_embeddings=num_maps, embedding_dim=MAP_EMBEDDING_DIM)
            combined_input_size = stats_input_size + MAP_EMBEDDING_DIM
            self.net = nn.Sequential(
                nn.Linear(combined_input_size, 1024),
                nn.BatchNorm1d(1024),
                nn.ReLU(),
                nn.Dropout(0.4),
                nn.Linear(1024, 512),
                nn.BatchNorm1d(512),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(512, 128),
                nn.ReLU(),
                nn.Linear(128, 1),
            )

        def forward(self, x_stats, x_map):
            embs = self.map_embedding(x_map)
            combined = torch.cat([x_stats, embs], dim=1)
            return self.net(combined)

    return WinPredictorWithMap(num_maps=num_maps, stats_input_size=stats_input_size)


async def _get_artifacts() -> _Artifacts:
    global _ARTIFACTS
    if _ARTIFACTS is not None:
        return _ARTIFACTS

    async with _ARTIFACTS_LOCK:
        if _ARTIFACTS is not None:
            return _ARTIFACTS

        try:
            import torch
            import joblib
        except Exception as e:
            logger.exception("ML imports failed (torch/joblib missing?)")
            raise HTTPException(
                status_code=503,
                detail=f"ML dependencies missing in API env: {e}. Install torch + joblib + scikit-learn + numpy.",
            )

        # Priorité: variables d'env -> artifacts de ../ml -> fallback api/model
        model_path = _resolve_artifact_path(
            settings.model_path,
            "model/wot_model_map.pth",
        )
        scaler_path = _resolve_artifact_path(
            settings.scaler_path,
            "model/scaler.pkl",
        )
        map_index_path = _resolve_artifact_path(
            settings.map_index_path,
            "model/map_index.pkl",
        )

        map_index = joblib.load(str(map_index_path))
        if not isinstance(map_index, dict) or len(map_index) < 1:
            logger.error("map_index.pkl invalid: %s", str(map_index_path))
            raise HTTPException(status_code=500, detail="map_index.pkl is invalid")

        # Convertit clés en int (csv 'map' est numérique)
        map_index_int: Dict[int, int] = {}
        for k, v in map_index.items():
            try:
                map_index_int[int(k)] = int(v)
            except Exception:
                continue
        if not map_index_int:
            raise HTTPException(status_code=500, detail="map_index.pkl contains no usable entries")

        scaler = joblib.load(str(scaler_path))

        stats_dim = MAX_PLAYERS * len(FEATURE_COLS) * 2
        num_maps = max(map_index_int.values()) + 1
        model = _make_model(num_maps=num_maps, stats_input_size=stats_dim)

        try:
            state = torch.load(str(model_path), map_location="cpu")
        except Exception as e:
            logger.exception("torch.load failed for model: %s", str(model_path))
            raise HTTPException(status_code=500, detail=f"Failed to load model file: {e}")
        if not isinstance(state, dict):
            logger.error("Model file is not a state_dict: %s", str(model_path))
            raise HTTPException(status_code=500, detail="wot_model_map.pth is not a state_dict")
        model.load_state_dict(state)
        model.eval()

        _ARTIFACTS = _Artifacts(model=model, scaler=scaler, map_index=map_index_int)
        return _ARTIFACTS


def _build_stats_from_tomato_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Reproduit le schéma 'stats' du mod (StatsFetcher._get_player_stats)."""
    data = (payload or {}).get("data") or {}
    if not isinstance(data, dict):
        return {}

    # Réduire la taille (retirer 'tanks') comme le mod
    try:
        data_slim = dict(data)
        if "tanks" in data_slim:
            del data_slim["tanks"]
    except Exception:
        data_slim = data

    return {
        "tomato_overall": data_slim,
        "battles": data.get("battles"),
        "wins": data.get("wins"),
        "losses": data.get("losses"),
        "overallWN8": data.get("overallWN8"),
        "overallWNX": data.get("overallWNX"),
        "winrate": data.get("winrate"),
        "dpg": data.get("dpg"),
        "assist": data.get("assist"),
        "frags": data.get("frags"),
        "survival": data.get("survival"),
        "spots": data.get("spots"),
        "cap": data.get("cap"),
        "def": data.get("def"),
        "xp": data.get("xp"),
        "kd": data.get("kd"),
        "total_damage": data.get("totalDamage"),
        "total_frags": data.get("totalFrags"),
    }


async def _resolve_account_ids_via_wg_route(pseudos: List[str], region: str) -> Tuple[Dict[str, int], Dict[str, str]]:
    """Résout nickname -> account_id en appelant la route interne wg/account/list."""
    normalized = _normalize_pseudos(pseudos)
    if not normalized:
        raise HTTPException(status_code=400, detail="pseudos must contain at least one non-empty value")

    # Tentative batch 'exact' (nick1,nick2,...) comme le mod
    search = ",".join(normalized)
    resp = await wg_account_list(
        search=search,
        type="exact",
        limit=min(len(normalized), 100),
        region=region,
    )

    if not isinstance(resp, dict) or resp.get("status") != "ok":
        raise HTTPException(status_code=502, detail="WG account/list proxy returned error")

    candidates = resp.get("data") or []
    by_name: Dict[str, Dict[str, Any]] = {}
    for p in candidates:
        if isinstance(p, dict) and p.get("nickname"):
            by_name[str(p.get("nickname"))] = p

    resolved: Dict[str, int] = {}
    missing: Dict[str, str] = {}
    for name in normalized:
        p = by_name.get(name)
        if not p:
            missing[name] = "wg_not_found"
            continue
        account_id = p.get("account_id")
        if not account_id:
            missing[name] = "wg_missing_account_id"
            continue
        try:
            resolved[name] = int(account_id)
        except Exception:
            missing[name] = "wg_invalid_account_id"

    return resolved, missing


async def _fetch_tomato_overall_via_route(account_id: int, server: str) -> Optional[Dict[str, Any]]:
    try:
        payload = await tomato_player_overall(server=server, account_id=int(account_id))
        if isinstance(payload, dict):
            return payload
    except HTTPException:
        raise
    except Exception:
        return None
    return None


async def _build_prediction_features(pseudos: List[str], spawn: int, region: Optional[str]) -> PredictFeaturesResponse:
    resolved_region = (region or settings.wargaming_region or "eu").lower()
    if resolved_region not in WG_BASE_URLS:
        raise HTTPException(status_code=400, detail=f"Invalid region: {resolved_region}")

    if spawn not in (1, 2):
        raise HTTPException(status_code=400, detail="spawn must be 1 or 2")

    account_ids, missing = await _resolve_account_ids_via_wg_route(pseudos, resolved_region)
    tomato_server = resolved_region

    # Concurrence raisonnable (évite de spammer Tomato)
    sem = asyncio.Semaphore(8)

    async def _one(name: str, aid: int) -> Tuple[str, Optional[Dict[str, Any]]]:
        async with sem:
            payload = await _fetch_tomato_overall_via_route(aid, tomato_server)
            return name, payload

    tasks = [_one(name, aid) for (name, aid) in account_ids.items()]
    results: List[Tuple[str, Optional[Dict[str, Any]]]] = await asyncio.gather(*tasks, return_exceptions=False)

    players: Dict[str, Dict[str, Any]] = {}
    for name, payload in results:
        if not payload:
            missing[name] = "tomato_failed"
            continue

        stats = _build_stats_from_tomato_payload(payload)
        if not stats:
            missing[name] = "tomato_invalid_payload"
            continue

        players[name] = {
            "account_id": account_ids.get(name),
            "stats": stats,
        }

    return PredictFeaturesResponse(
        user="",
        user_spawn=spawn,
        region=resolved_region,
        players=players,
        missing_players=missing,
    )


async def _build_prediction_features_from_request(
    payload: PredictWinRequest,
    *,
    region: Optional[str],
    map_id: Optional[int],
) -> PredictFeaturesResponse:
    team1, team2 = _split_teams_from_request(payload)
    all_names = _normalize_pseudos((team1 + team2) or (payload.pseudos or []))
    if not all_names:
        raise HTTPException(status_code=400, detail="No players provided (spawn_1/spawn_2/players/pseudos)")

    features = await _build_prediction_features(all_names, payload.user_spawn, region)
    features.user = payload.user
    features.user_spawn = payload.user_spawn

    if map_id is not None:
        features.map_id = int(map_id)
        try:
            artifacts = await _get_artifacts()
            idx = artifacts.map_index.get(int(map_id))
            features.map_index = int(idx) if idx is not None else 0
            features.map_unknown = idx is None
        except HTTPException:
            features.map_index = 0
            features.map_unknown = True

    return features


async def _predict_win_from_features(
    *,
    map_id: int,
    user_spawn: int,
    user: str,
    team1_names: List[str],
    team2_names: List[str],
    features: PredictFeaturesResponse,
) -> bool:
    artifacts = await _get_artifacts()

    map_idx = artifacts.map_index.get(int(map_id))
    map_unknown = map_idx is None
    if map_unknown:
        # Fallback simple: index 0 (permet de prédire même si map inconnue)
        map_idx = 0

    # Construire les matrices "joueurs" pour chaque équipe à partir des stats Tomato
    def _stats_for(name: str) -> Dict[str, Any]:
        p = features.players.get(name) or {}
        stats = p.get("stats") or {}
        return stats if isinstance(stats, dict) else {}

    team1_stats = [_stats_for(n) for n in team1_names]
    team2_stats = [_stats_for(n) for n in team2_names]

    vec1 = _get_padded_team_vector(team1_stats)
    vec2 = _get_padded_team_vector(team2_stats)
    x_stats = vec1 + vec2  # 390

    try:
        import numpy as np
        import torch
    except Exception as e:
        logger.exception("ML imports failed (numpy/torch missing?)")
        raise HTTPException(status_code=503, detail=f"ML dependencies missing in API env: {e}")

    x_np = np.asarray([x_stats], dtype=np.float32)
    try:
        x_scaled = artifacts.scaler.transform(x_np)
    except Exception as e:
        logger.exception("Scaler transform failed")
        raise HTTPException(status_code=500, detail=f"Scaler transform failed: {e}")

    x_tensor = torch.tensor(x_scaled, dtype=torch.float32)
    map_tensor = torch.tensor([int(map_idx)], dtype=torch.long)

    with torch.no_grad():
        logits = artifacts.model(x_tensor, map_tensor)
        prob_spawn1 = torch.sigmoid(logits).item()

    # Le modèle est entraîné sur la cible "spawn_1 gagne" (cf ml/data CSV, target).
    prob_user = prob_spawn1 if user_spawn == 1 else (1.0 - prob_spawn1)
    return bool(prob_user > 0.5)


@app.get(f"{settings.api_prefix}{settings.route_health}")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get(f"{settings.api_prefix}/predict/win", response_model=bool)
async def predict_win_get(
    user: str = Query(..., description="Pseudo utilisateur courant"),
    user_spawn: int = Query(..., ge=1, le=2, description="Spawn/équipe de l'utilisateur courant: 1 ou 2"),
    region: Optional[str] = Query(None, description="Région WG/Tomato: eu|na|ru|asia (défaut: settings)"),
    map_id: Optional[int] = Query(None, description="ID numérique de la map (colonne 'map' dans les CSV)", ge=0),
    spawn_1: Optional[str] = Query(None, description="Pseudos spawn_1 séparés par virgules"),
    spawn_2: Optional[str] = Query(None, description="Pseudos spawn_2 séparés par virgules"),
    pseudos: Optional[str] = Query(None, description="Fallback: 30 pseudos séparés par virgules (15/15)"),
) -> bool:
    if map_id is None:
        raise HTTPException(status_code=400, detail="map_id is required for model inference")

    team1 = _parse_csv_list(spawn_1)
    team2 = _parse_csv_list(spawn_2)
    if not team1 and not team2:
        all_list = _parse_csv_list(pseudos)
        team1 = all_list[:MAX_PLAYERS]
        team2 = all_list[MAX_PLAYERS : MAX_PLAYERS * 2]

    payload = PredictWinRequestWithPlayers(
        user=user,
        user_spawn=user_spawn,
        map_id=map_id,
        spawn_1=team1,
        spawn_2=team2,
        pseudos=(team1 + team2),
    )

    features = await _build_prediction_features_from_request(payload, region=region, map_id=map_id)
    return await _predict_win_from_features(
        map_id=int(map_id),
        user_spawn=user_spawn,
        user=user,
        team1_names=team1,
        team2_names=team2,
        features=features,
    )


@app.post(f"{settings.api_prefix}/predict/win", response_model=bool)
async def predict_win_post(
    payload: PredictWinRequestWithPlayers = Body(...),
    region: Optional[str] = Query(None, description="Région WG/Tomato: eu|na|ru|asia (défaut: settings)"),
) -> bool:
    if payload.map_id is None:
        raise HTTPException(status_code=400, detail="map_id is required for model inference")

    team1, team2 = _split_teams_from_request(payload)
    features = await _build_prediction_features_from_request(payload, region=region, map_id=payload.map_id)
    predicted = await _predict_win_from_features(
        map_id=int(payload.map_id),
        user_spawn=payload.user_spawn,
        user=payload.user,
        team1_names=team1,
        team2_names=team2,
        features=features,
    )
    return predicted


@app.get(f"{settings.api_prefix}/predict/features", response_model=PredictFeaturesResponse)
async def predict_features_get(
    user: str = Query(..., description="Pseudo utilisateur courant"),
    user_spawn: int = Query(..., ge=1, le=2, description="Spawn/équipe de l'utilisateur courant: 1 ou 2"),
    region: Optional[str] = Query(None, description="Région WG/Tomato: eu|na|ru|asia (défaut: settings)"),
    map_id: Optional[int] = Query(None, description="ID numérique de la map (colonne 'map' dans les CSV)", ge=0),
    spawn_1: Optional[str] = Query(None, description="Pseudos spawn_1 séparés par virgules"),
    spawn_2: Optional[str] = Query(None, description="Pseudos spawn_2 séparés par virgules"),
    pseudos: Optional[str] = Query(None, description="Fallback: 30 pseudos séparés par virgules (15/15)"),
) -> PredictFeaturesResponse:
    team1 = _parse_csv_list(spawn_1)
    team2 = _parse_csv_list(spawn_2)
    if not team1 and not team2:
        all_list = _parse_csv_list(pseudos)
        team1 = all_list[:MAX_PLAYERS]
        team2 = all_list[MAX_PLAYERS : MAX_PLAYERS * 2]

    payload = PredictWinRequestWithPlayers(
        user=user,
        user_spawn=user_spawn,
        map_id=map_id,
        spawn_1=team1,
        spawn_2=team2,
        pseudos=(team1 + team2),
    )
    return await _build_prediction_features_from_request(payload, region=region, map_id=map_id)


@app.post(f"{settings.api_prefix}/predict/features", response_model=PredictFeaturesResponse)
async def predict_features_post(
    payload: PredictWinRequestWithPlayers = Body(...),
    region: Optional[str] = Query(None, description="Région WG/Tomato: eu|na|ru|asia (défaut: settings)"),
) -> PredictFeaturesResponse:
    return await _build_prediction_features_from_request(payload, region=region, map_id=payload.map_id)


@app.get(f"{settings.api_prefix}/wg/account/list")
async def wg_account_list(
    search: str,
    type: str = "exact",
    limit: int = 100,
    region: Optional[str] = None,
) -> Any:
    """Proxy dédié: Wargaming `account/list/`.

    Une route dédiée par appel externe utilisé par le mod.
    """

    resolved_region = (region or settings.wargaming_region or "eu").lower()
    base = WG_BASE_URLS.get(resolved_region)
    if not base:
        raise HTTPException(status_code=400, detail=f"Invalid region: {resolved_region}")

    if not settings.wargaming_app_id:
        raise HTTPException(status_code=500, detail="WARGAMING_APP_ID is not configured")

    if limit < 1:
        raise HTTPException(status_code=400, detail="limit must be >= 1")
    if limit > 100:
        limit = 100

    target_url = f"{base}/account/list/"
    timeout = httpx.Timeout(settings.http_timeout_seconds)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            resp = await client.get(
                target_url,
                params={
                    "application_id": settings.wargaming_app_id,
                    "search": search,
                    "type": type,
                    "limit": limit,
                },
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Upstream WG request failed: {exc}") from exc

    try:
        return resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Upstream WG returned non-JSON")


@app.get(f"{settings.api_prefix}/tomato/player/overall/{'{server}'}/{'{account_id}'}")
async def tomato_player_overall(
    server: str,
    account_id: int,
) -> Any:
    """Proxy dédié: Tomato.gg `player/overall/{server}/{account_id}`."""

    base = (settings.tomato_api_base_url or "").rstrip("/")
    if not base:
        raise HTTPException(status_code=500, detail="TOMATO_API_BASE_URL is not configured")

    target_url = f"{base}/player/overall/{server}/{account_id}"
    timeout = httpx.Timeout(settings.http_timeout_seconds)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            resp = await client.get(target_url)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Upstream Tomato request failed: {exc}") from exc

    try:
        return resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Upstream Tomato returned non-JSON")
