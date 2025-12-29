from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import AliasChoices, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
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


settings = Settings()

app = FastAPI(title=settings.api_title)


WG_BASE_URLS: Dict[str, str] = {
    "eu": "https://api.worldoftanks.eu/wot",
    "na": "https://api.worldoftanks.com/wot",
    "ru": "https://api.worldoftanks.ru/wot",
    "asia": "https://api.worldoftanks.asia/wot",
}
class HttpRequest(BaseModel):
    pass


@app.get(f"{settings.api_prefix}{settings.route_health}")
def health() -> Dict[str, str]:
    return {"status": "ok"}


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
