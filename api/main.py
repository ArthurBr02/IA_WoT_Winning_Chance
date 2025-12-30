from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import asyncio
import hashlib
from pathlib import Path
import time
import logging
import os

import httpx
from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import AliasChoices, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


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

# Ensure logs appear under uvicorn (which configures handlers) and also when running directly.
# Uvicorn may set loggers to WARNING depending on its config; we force our logger level via LOG_LEVEL.
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=_LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

for _name in ("uvicorn.error", "uvicorn.access", "wot_api"):
    logging.getLogger(_name).setLevel(_LOG_LEVEL)

logger = logging.getLogger("wot_api")

app = FastAPI(title=settings.api_title)


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    req_id = hashlib.sha1(f"{time.time_ns()}-{request.url}".encode("utf-8")).hexdigest()[:12]
    logger.warning("request_validation_error id=%s url=%s errors=%s", req_id, str(request.url), str(exc.errors()))
    return JSONResponse(status_code=422, content={"detail": exc.errors(), "request_id": req_id})


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    req_id = hashlib.sha1(f"{time.time_ns()}-{request.url}".encode("utf-8")).hexdigest()[:12]
    logger.exception("unhandled_exception id=%s url=%s", req_id, str(request.url))
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "request_id": req_id})


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


class PredictWinResponse(BaseModel):
    predicted: bool = Field(..., description="Prédiction binaire: True=victoire, False=défaite (pour l'utilisateur courant)")
    prob_user: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Probabilité de victoire pour l'utilisateur courant, en pourcentage (0-100)",
    )


# Pydantic v2 + postponed annotations:
# ensure all models are fully rebuilt before FastAPI uses them for request parsing.
try:
    PredictWinRequest.model_rebuild()
    PlayerWithSpawn.model_rebuild()
    PredictWinRequestWithPlayers.model_rebuild()
    PredictFeaturesResponse.model_rebuild()
    PredictWinResponse.model_rebuild()
except Exception:
    # Don't crash the app at import time; failing here would otherwise turn every request into a 500.
    pass


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
# Must match ml/main.py (current training uses MAP_EMBEDDING_DIM = 16)
MAP_EMBEDDING_DIM: int = 16

# Must match ml/main.py
GLOBAL_FEATURES: Tuple[str, ...] = (
    "delta_mean_wn8",
    "delta_mean_wr",
    "delta_top3_wn8",
    "delta_sum_battles",
    "delta_mean_dpg",
    "delta_mean_xp",
)


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


def _safe_mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / max(1, len(values)))


def _safe_topk_mean(values: List[float], k: int) -> float:
    if not values:
        return 0.0
    return float(sum(values[:k]) / max(1, min(k, len(values))))


def _compute_global_features(team1_stats: List[Dict[str, Any]], team2_stats: List[Dict[str, Any]]) -> List[float]:
    """Compute engineered global features for a match: (team1 - team2).

    Mirrors ml/main.py::compute_global_features.
    """
    t1_wn8 = sorted([_safe_float(p.get("overallWN8")) for p in team1_stats], reverse=True)
    t2_wn8 = sorted([_safe_float(p.get("overallWN8")) for p in team2_stats], reverse=True)

    delta_mean_wn8 = _safe_mean(t1_wn8) - _safe_mean(t2_wn8)
    delta_mean_wr = _safe_mean([_safe_float(p.get("winrate")) for p in team1_stats]) - _safe_mean(
        [_safe_float(p.get("winrate")) for p in team2_stats]
    )
    delta_top3_wn8 = _safe_topk_mean(t1_wn8, 3) - _safe_topk_mean(t2_wn8, 3)
    delta_sum_battles = sum([_safe_float(p.get("battles")) for p in team1_stats]) - sum(
        [_safe_float(p.get("battles")) for p in team2_stats]
    )
    delta_mean_dpg = _safe_mean([_safe_float(p.get("dpg")) for p in team1_stats]) - _safe_mean(
        [_safe_float(p.get("dpg")) for p in team2_stats]
    )
    delta_mean_xp = _safe_mean([_safe_float(p.get("xp")) for p in team1_stats]) - _safe_mean(
        [_safe_float(p.get("xp")) for p in team2_stats]
    )

    return [
        float(delta_mean_wn8),
        float(delta_mean_wr),
        float(delta_top3_wn8),
        float(delta_sum_battles),
        float(delta_mean_dpg),
        float(delta_mean_xp),
    ]


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


def _get_padded_team_matrix(team_stats: List[Dict[str, Any]]) -> List[List[float]]:
    """Return (MAX_PLAYERS, num_features) sorted + padded (matches ml/main.py)."""
    sorted_team = sorted(team_stats, key=lambda d: _safe_float(d.get("overallWN8")), reverse=True)
    rows: List[List[float]] = []
    for p in sorted_team[:MAX_PLAYERS]:
        rows.append([_safe_float(p.get(col)) for col in FEATURE_COLS])
    while len(rows) < MAX_PLAYERS:
        rows.append([0.0] * len(FEATURE_COLS))
    return rows


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
    raise FileNotFoundError(f"No valid artifact path found among candidates: {candidates}")


class _Artifacts:
    def __init__(
        self,
        model: Any,
        players_scaler: Any,
        global_scaler: Any,
        global_features: Tuple[str, ...],
        map_index: Dict[int, int],
        model_type: str,
    ):
        self.model = model
        self.players_scaler = players_scaler
        self.global_scaler = global_scaler
        self.global_features = global_features
        self.map_index = map_index
        self.model_type = model_type


def _infer_model_type_from_state_dict(state: Dict[str, Any]) -> str:
    keys = list(state.keys())
    if any(k.startswith("stats_cnn.") for k in keys):
        return "cnn"
    if any(k.startswith("player_encoder.") for k in keys) or any(k.startswith("map_emb.") for k in keys):
        return "attention"
    if any(k.startswith("phi.") for k in keys):
        return "deepset"
    # legacy MLP (old api)
    return "mlp"


def _infer_num_maps_from_state_dict(state: Dict[str, Any]) -> Optional[int]:
    for k in ("map_embedding.weight", "map_emb.weight"):
        w = state.get(k)
        try:
            if hasattr(w, "shape") and len(w.shape) == 2:
                return int(w.shape[0])
        except Exception:
            continue
    return None


_ARTIFACTS: Optional[_Artifacts] = None
_ARTIFACTS_LOCK = asyncio.Lock()


def _make_model(model_type: str, num_maps: int, *, num_features: int, stats_input_size: int):
    import torch
    import torch.nn as nn

    class WinPredictorCNNWithMap(nn.Module):
        def __init__(self, num_maps: int):
            super().__init__()
            self.map_embedding = nn.Embedding(num_embeddings=num_maps, embedding_dim=MAP_EMBEDDING_DIM)
            self.stats_cnn = nn.Sequential(
                nn.Conv2d(1, 32, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                nn.Conv2d(32, 32, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=(2, 1)),
                nn.Dropout2d(0.10),
                nn.Conv2d(32, 64, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.Conv2d(64, 64, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=(2, 1)),
                nn.Dropout2d(0.15),
                nn.Conv2d(64, 128, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(128),
                nn.ReLU(inplace=True),
                nn.AdaptiveAvgPool2d((1, 1)),
            )
            combined_input_size = 128 + MAP_EMBEDDING_DIM + len(GLOBAL_FEATURES)
            self.head = nn.Sequential(
                nn.Linear(combined_input_size, 128),
                nn.ReLU(inplace=True),
                nn.Dropout(0.25),
                nn.Linear(128, 1),
            )

        def forward(self, x_stats_grid, x_map, x_global):
            stats_feat = self.stats_cnn(x_stats_grid).flatten(1)
            embs = self.map_embedding(x_map)
            combined = torch.cat([stats_feat, embs, x_global], dim=1)
            return self.head(combined)

    class WinPredictorAttention(nn.Module):
        def __init__(self, num_maps: int, num_features: int):
            super().__init__()
            self.map_emb = nn.Embedding(num_maps, MAP_EMBEDDING_DIM)
            self.player_encoder = nn.Sequential(
                nn.Linear(num_features, 128),
                nn.LayerNorm(128),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(128, 128),
                nn.ReLU(),
            )
            self.attn = nn.Sequential(
                nn.Linear(128, 64),
                nn.Tanh(),
                nn.Linear(64, 1),
            )
            combined_dim = (128 * 3) + MAP_EMBEDDING_DIM + len(GLOBAL_FEATURES)
            self.head = nn.Sequential(
                nn.Linear(combined_dim, 256),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(256, 1),
            )

        def get_team_embedding(self, x, mask):
            enc = self.player_encoder(x)
            scores = self.attn(enc)
            scores = scores.masked_fill(mask == 0, -1e9)
            weights = torch.softmax(scores, dim=1)
            return torch.sum(enc * weights, dim=1)

        def forward(self, x_stats, x_map, x_global):
            if x_stats.ndim == 4:
                x_stats = x_stats.squeeze(1)
            t1 = x_stats[:, :MAX_PLAYERS, :]
            t2 = x_stats[:, MAX_PLAYERS:, :]
            m1 = (t1.abs().sum(dim=-1, keepdim=True) > 0).float()
            m2 = (t2.abs().sum(dim=-1, keepdim=True) > 0).float()
            emb1 = self.get_team_embedding(t1, m1)
            emb2 = self.get_team_embedding(t2, m2)
            map_v = self.map_emb(x_map)
            feat_diff = emb1 - emb2
            combined = torch.cat([emb1, emb2, feat_diff, map_v, x_global], dim=1)
            return self.head(combined)

    class AttentionPooling(nn.Module):
        def __init__(self, input_dim: int):
            super().__init__()
            self.attn_net = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.Tanh(),
                nn.Linear(64, 1),
            )

        def forward(self, x, mask):
            scores = self.attn_net(x)
            scores = scores.masked_fill(mask == 0, -1e9)
            weights = torch.softmax(scores, dim=1)
            return torch.sum(x * weights, dim=1)

    class WinPredictorDeepSetWithMap(nn.Module):
        def __init__(self, num_maps: int, num_features: int):
            super().__init__()
            self.num_features = int(num_features)
            self.map_embedding = nn.Embedding(num_embeddings=num_maps, embedding_dim=MAP_EMBEDDING_DIM)
            phi_dim = 128
            self.phi = nn.Sequential(
                nn.Linear(self.num_features, 128),
                nn.ReLU(inplace=True),
                nn.Dropout(0.10),
                nn.Linear(128, phi_dim),
                nn.ReLU(inplace=True),
            )
            self.pool_t1 = AttentionPooling(phi_dim)
            self.pool_t2 = AttentionPooling(phi_dim)
            combined_dim = (phi_dim * 4) + MAP_EMBEDDING_DIM + len(GLOBAL_FEATURES)
            self.head = nn.Sequential(
                nn.Linear(combined_dim, 256),
                nn.ReLU(inplace=True),
                nn.Dropout(0.25),
                nn.Linear(256, 64),
                nn.ReLU(inplace=True),
                nn.Dropout(0.15),
                nn.Linear(64, 1),
            )

        def forward(self, x_stats_grid, x_map, x_global):
            if x_stats_grid.ndim == 4:
                x = x_stats_grid.squeeze(1)
            else:
                x = x_stats_grid
            mask = (x.abs().sum(dim=-1, keepdim=True) > 0).float()
            b, p, f = x.shape
            x_flat = x.reshape(b * p, f)
            e_flat = self.phi(x_flat)
            e = e_flat.reshape(b, p, -1)
            e1, e2 = e[:, :MAX_PLAYERS, :], e[:, MAX_PLAYERS : MAX_PLAYERS * 2, :]
            m1, m2 = mask[:, :MAX_PLAYERS, :], mask[:, MAX_PLAYERS : MAX_PLAYERS * 2, :]
            t1 = self.pool_t1(e1, m1)
            t2 = self.pool_t2(e2, m2)
            pair = torch.cat([t1, t2, (t1 - t2), (t1 * t2)], dim=1)
            embs = self.map_embedding(x_map)
            combined = torch.cat([pair, embs, x_global], dim=1)
            return self.head(combined)

    class WinPredictorWithMapMLP(nn.Module):
        def __init__(self, num_maps: int, stats_input_size: int):
            super().__init__()
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

    if model_type == "cnn":
        return WinPredictorCNNWithMap(num_maps=num_maps)
    if model_type == "attention":
        return WinPredictorAttention(num_maps=num_maps, num_features=num_features)
    if model_type == "deepset":
        return WinPredictorDeepSetWithMap(num_maps=num_maps, num_features=num_features)
    return WinPredictorWithMapMLP(num_maps=num_maps, stats_input_size=stats_input_size)


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

        # Priorité: variables d'env -> ../ml (latest trained) -> fallback api/model (legacy)
        model_path = _resolve_artifact_path(
            settings.model_path,
            "../ml/wot_model_map.pth",
            "model/wot_model_map.pth",
        )
        scaler_path = _resolve_artifact_path(
            settings.scaler_path,
            "../ml/scaler.pkl",
            "model/scaler.pkl",
        )
        map_index_path = _resolve_artifact_path(
            settings.map_index_path,
            "../ml/map_index.pkl",
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

        try:
            state = torch.load(str(model_path), map_location="cpu")
        except Exception as e:
            logger.exception("torch.load failed for model: %s", str(model_path))
            raise HTTPException(status_code=500, detail=f"Failed to load model file: {e}")
        if not isinstance(state, dict):
            logger.error("Model file is not a state_dict: %s", str(model_path))
            raise HTTPException(status_code=500, detail="wot_model_map.pth is not a state_dict")

        scaler_obj = joblib.load(str(scaler_path))
        if isinstance(scaler_obj, dict):
            players_scaler = scaler_obj.get("players")
            global_scaler = scaler_obj.get("global")
            global_features = tuple(scaler_obj.get("global_features") or GLOBAL_FEATURES)
        else:
            # Backward compatible: old scaler.pkl contained only the players scaler
            players_scaler = scaler_obj
            global_scaler = None
            global_features = GLOBAL_FEATURES

        model_type = _infer_model_type_from_state_dict(state)
        stats_dim = MAX_PLAYERS * len(FEATURE_COLS) * 2
        inferred_num_maps = _infer_num_maps_from_state_dict(state)
        num_maps = inferred_num_maps or (max(map_index_int.values()) + 1)
        if inferred_num_maps is not None and inferred_num_maps != (max(map_index_int.values()) + 1):
            logger.info(
                "num_maps mismatch: state_dict=%d map_index=%d; using state_dict value",
                int(inferred_num_maps),
                int(max(map_index_int.values()) + 1),
            )

        model = _make_model(
            model_type=model_type,
            num_maps=num_maps,
            num_features=len(FEATURE_COLS),
            stats_input_size=stats_dim,
        )
        try:
            model.load_state_dict(state)
        except Exception as e:
            logger.exception(
                "model.load_state_dict failed model_path=%s model_type=%s num_maps=%d map_emb_dim=%d",
                str(model_path),
                str(model_type),
                int(num_maps),
                int(MAP_EMBEDDING_DIM),
            )
            raise HTTPException(status_code=500, detail=f"Model load_state_dict failed: {e}")
        model.eval()

        _ARTIFACTS = _Artifacts(
            model=model,
            players_scaler=players_scaler,
            global_scaler=global_scaler,
            global_features=global_features,
            map_index=map_index_int,
            model_type=model_type,
        )
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
    try:
        resp = await wg_account_list(
            search=search,
            type="exact",
            limit=min(len(normalized), 100),
            region=region,
        )
    except HTTPException as e:
        # Dégradation contrôlée: si WG est indisponible, on ne plante pas la prédiction.
        # On retournera des vecteurs de zéros => prédiction moins fiable mais l'UX reste fluide.
        logger.warning("WG proxy failed for account/list: %s", str(e.detail))
        missing = {name: "wg_proxy_failed" for name in normalized}
        return {}, missing

    if not isinstance(resp, dict) or resp.get("status") != "ok":
        # Dégradation contrôlée: si WG renvoie une erreur (ex: app_id invalide / rate-limit),
        # on continue la prédiction avec des vecteurs à zéro.
        try:
            status = resp.get("status") if isinstance(resp, dict) else None
            err = resp.get("error") if isinstance(resp, dict) else None
        except Exception:
            status = None
            err = None

        logger.warning(
            "WG account/list returned error status=%s error=%s region=%s search_count=%d",
            str(status),
            str(err),
            str(region),
            len(normalized),
        )
        missing = {name: "wg_error_response" for name in normalized}
        return {}, missing

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
    except HTTPException as e:
        # Important: ne pas propager en 502 global.
        logger.warning("Tomato proxy failed for account_id=%s: %s", str(account_id), str(e.detail))
        return None
    except Exception as e:
        logger.warning("Tomato fetch failed for account_id=%s: %s", str(account_id), str(e))
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
        try:
            async with sem:
                payload = await _fetch_tomato_overall_via_route(aid, tomato_server)
                return name, payload
        except Exception as e:
            logger.warning("Tomato task failed for %s (%s): %s", name, str(aid), str(e))
            return name, None

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

    t0 = time.perf_counter()
    features = await _build_prediction_features(all_names, payload.user_spawn, region)
    dt_ms = int((time.perf_counter() - t0) * 1000)
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

    logger.info(
        "features_built user=%s user_spawn=%s map_id=%s region=%s teams=(%d,%d) resolved=%d missing=%d dt_ms=%d",
        payload.user,
        payload.user_spawn,
        str(map_id) if map_id is not None else "None",
        features.region,
        len(team1),
        len(team2),
        len(features.players),
        len(features.missing_players),
        dt_ms,
    )

    return features


async def _predict_win_from_features(
    *,
    map_id: int,
    user_spawn: int,
    user: str,
    team1_names: List[str],
    team2_names: List[str],
    features: PredictFeaturesResponse,
) -> PredictWinResponse:
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

    # Player matrix (30, 13) like ml/main.py
    mat1 = _get_padded_team_matrix(team1_stats)
    mat2 = _get_padded_team_matrix(team2_stats)
    match_matrix = mat1 + mat2  # (30, 13)

    # Engineered global features (team1 - team2)
    global_feats = _compute_global_features(team1_stats, team2_stats)

    try:
        import numpy as np
        import torch
    except Exception as e:
        logger.exception("ML imports failed (numpy/torch missing?)")
        raise HTTPException(status_code=503, detail=f"ML dependencies missing in API env: {e}")

    x_np = np.asarray(match_matrix, dtype=np.float32).reshape(1, -1)
    try:
        x_scaled_flat = artifacts.players_scaler.transform(x_np)
    except Exception as e:
        logger.exception("Players scaler transform failed")
        raise HTTPException(status_code=500, detail=f"Players scaler transform failed: {e}")

    # (B, 1, 30, 13)
    x_grid = x_scaled_flat.reshape(1, 1, MAX_PLAYERS * 2, len(FEATURE_COLS)).astype(np.float32, copy=False)
    x_tensor = torch.tensor(x_grid, dtype=torch.float32)

    g_np = np.asarray([global_feats], dtype=np.float32)
    if artifacts.global_scaler is not None:
        try:
            g_scaled = artifacts.global_scaler.transform(g_np)
        except Exception as e:
            logger.exception("Global scaler transform failed")
            raise HTTPException(status_code=500, detail=f"Global scaler transform failed: {e}")
        g_tensor = torch.tensor(g_scaled, dtype=torch.float32)
    else:
        g_tensor = torch.tensor(g_np, dtype=torch.float32)
    map_tensor = torch.tensor([int(map_idx)], dtype=torch.long)

    with torch.no_grad():
        if artifacts.model_type == "mlp":
            # Legacy: expects flat (B, 390)
            logits = artifacts.model(torch.tensor(x_scaled_flat, dtype=torch.float32), map_tensor)
        else:
            logits = artifacts.model(x_tensor, map_tensor, g_tensor)
        prob_spawn1 = torch.sigmoid(logits).item()

    # Le modèle est entraîné sur la cible "spawn_1 gagne" (cf ml/data CSV, target).
    prob_user = prob_spawn1 if user_spawn == 1 else (1.0 - prob_spawn1)
    predicted = bool(prob_user > 0.5)

    # Exposer en pourcentage (0-100) pour le client (mod WoT).
    prob_user_pct = float(prob_user * 100.0)

    logger.info(
        "prediction user=%s user_spawn=%d map_id=%d map_unknown=%s teams=(%d,%d) resolved=%d missing=%d prob_spawn1=%.4f prob_user=%.4f predicted=%s",
        user,
        int(user_spawn),
        int(map_id),
        "1" if map_unknown else "0",
        len(team1_names),
        len(team2_names),
        len(features.players),
        len(features.missing_players),
        float(prob_spawn1),
        float(prob_user),
        str(predicted),
    )

    # Si utile pour debug, afficher un aperçu des erreurs (limité)
    if features.missing_players:
        try:
            items = list(features.missing_players.items())[:8]
            logger.info("missing_players_sample=%s", str(items))
        except Exception:
            pass

    return PredictWinResponse(predicted=predicted, prob_user=prob_user_pct)


@app.get(f"{settings.api_prefix}{settings.route_health}")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get(f"{settings.api_prefix}/predict/win", response_model=PredictWinResponse)
async def predict_win_get(
    user: str = Query(..., description="Pseudo utilisateur courant"),
    user_spawn: int = Query(..., ge=1, le=2, description="Spawn/équipe de l'utilisateur courant: 1 ou 2"),
    region: Optional[str] = Query(None, description="Région WG/Tomato: eu|na|ru|asia (défaut: settings)"),
    map_id: Optional[int] = Query(None, description="ID numérique de la map (colonne 'map' dans les CSV)", ge=0),
    spawn_1: Optional[str] = Query(None, description="Pseudos spawn_1 séparés par virgules"),
    spawn_2: Optional[str] = Query(None, description="Pseudos spawn_2 séparés par virgules"),
    pseudos: Optional[str] = Query(None, description="Fallback: 30 pseudos séparés par virgules (15/15)"),
) -> PredictWinResponse:
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
    result = await _predict_win_from_features(
        map_id=int(map_id),
        user_spawn=user_spawn,
        user=user,
        team1_names=team1,
        team2_names=team2,
        features=features,
    )
    logger.info("predict_win_result user=%s predicted=%s prob_user_pct=%.2f", user, str(result.predicted), float(result.prob_user))
    return result


@app.post(f"{settings.api_prefix}/predict/win", response_model=PredictWinResponse)
async def predict_win_post(
    payload: PredictWinRequestWithPlayers = Body(...),
    region: Optional[str] = Query(None, description="Région WG/Tomato: eu|na|ru|asia (défaut: settings)"),
) -> PredictWinResponse:
    # Log du body (pour réplication). Ne contient que pseudos/spawns/map => safe.
    try:
        body = payload.model_dump(mode="json")
        logger.info(
            "predict_win_request region=%s body=%s",
            str(region or settings.wargaming_region or "eu"),
            json.dumps(body, ensure_ascii=False, sort_keys=True),
        )
    except Exception:
        pass

    try:
        if payload.map_id is None:
            raise HTTPException(status_code=400, detail="map_id is required for model inference")

        team1, team2 = _split_teams_from_request(payload)
        features = await _build_prediction_features_from_request(payload, region=region, map_id=payload.map_id)
        result = await _predict_win_from_features(
            map_id=int(payload.map_id),
            user_spawn=payload.user_spawn,
            user=payload.user,
            team1_names=team1,
            team2_names=team2,
            features=features,
        )
        logger.info(
            "predict_win_result user=%s predicted=%s prob_user_pct=%.2f",
            payload.user,
            str(result.predicted),
            float(result.prob_user),
        )
        return result
    except HTTPException as e:
        try:
            body = payload.model_dump(mode="json")
            logger.warning(
                "predict_win_error status=%d detail=%s region=%s body=%s",
                int(e.status_code),
                str(e.detail),
                str(region or settings.wargaming_region or "eu"),
                json.dumps(body, ensure_ascii=False, sort_keys=True),
            )
        except Exception:
            pass
        raise
    except Exception:
        try:
            body = payload.model_dump(mode="json")
            logger.exception(
                "predict_win_unhandled_error region=%s body=%s",
                str(region or settings.wargaming_region or "eu"),
                json.dumps(body, ensure_ascii=False, sort_keys=True),
            )
        except Exception:
            logger.exception("predict_win_unhandled_error (failed to dump body)")
        raise HTTPException(status_code=500, detail="Internal prediction error")


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
            logger.exception(
                "Upstream WG request failed url=%s region=%s search=%s",
                target_url,
                resolved_region,
                search,
            )
            raise HTTPException(status_code=502, detail=f"Upstream WG request failed: {exc}") from exc

    try:
        return resp.json()
    except ValueError:
        logger.error("Upstream WG returned non-JSON url=%s status=%s", target_url, str(resp.status_code))
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
            logger.exception("Upstream Tomato request failed url=%s", target_url)
            raise HTTPException(status_code=502, detail=f"Upstream Tomato request failed: {exc}") from exc

    try:
        return resp.json()
    except ValueError:
        logger.error("Upstream Tomato returned non-JSON url=%s status=%s", target_url, str(resp.status_code))
        raise HTTPException(status_code=502, detail="Upstream Tomato returned non-JSON")
