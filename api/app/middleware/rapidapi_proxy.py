"""Validación RapidAPI Proxy-Secret + whitelist de rutas del Hub."""

from __future__ import annotations

import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings

# Rutas permitidas en el Hub RapidAPI (BASIC+PRO + extras ULTRA/MEGA).
# El filtrado Free vs Ultra de cara al consumidor se hace en Studio (qué endpoints
# aparecen en cada pack). Aquí bloqueamos admin/ingest/etc.
_HUB_ALLOW: list[tuple[str, re.Pattern[str]]] = [
    ("GET", re.compile(r"^/v1/health/?$")),
    ("GET", re.compile(r"^/v1/ready/?$")),
    ("GET", re.compile(r"^/v1/chains/?$")),
    ("GET", re.compile(r"^/v1/whales/?$")),
    ("GET", re.compile(r"^/v1/whales/tx/[^/]+/?$")),
    ("GET", re.compile(r"^/v1/whales/[^/]+/?$")),
    ("GET", re.compile(r"^/v1/stats/overview/?$")),
    ("GET", re.compile(r"^/v1/stats/timeseries/?$")),
    ("GET", re.compile(r"^/v1/entities/[^/]+/?$")),
    ("GET", re.compile(r"^/v1/market/assets/?$")),
    ("GET", re.compile(r"^/v1/market/analysis/?$")),
]

_OPEN_WITHOUT_SECRET = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def _is_open_path(path: str) -> bool:
    return any(path.endswith(p) or path == p for p in _OPEN_WITHOUT_SECRET) or path.startswith("/docs")


def is_hub_allowed(method: str, path: str) -> bool:
    for m, pattern in _HUB_ALLOW:
        if method.upper() == m and pattern.match(path):
            return True
    return False


class RapidApiProxyMiddleware(BaseHTTPMiddleware):
    """
    - Si RAPIDAPI_PROXY_SECRET está vacío: no hace nada (dev).
    - Si el request trae X-RapidAPI-Proxy-Secret incorrecto → 403.
    - Si RAPIDAPI_REQUIRE_PROXY=true → exige secret en casi todas las rutas.
    - Si el request viene con secret válido y RAPIDAPI_HUB_ONLY=true → solo whitelist Hub.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        settings = get_settings()
        secret = (settings.rapidapi_proxy_secret or "").strip()
        path = request.url.path
        provided = request.headers.get("x-rapidapi-proxy-secret")

        if not secret:
            return await call_next(request)

        if _is_open_path(path):
            return await call_next(request)

        # Secret incorrecto siempre se rechaza
        if provided is not None and provided != secret:
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid X-RapidAPI-Proxy-Secret"},
            )

        require_proxy = settings.rapidapi_require_proxy or (
            settings.app_env == "production" and settings.rapidapi_enforce_in_production
        )
        if require_proxy and provided != secret:
            return JSONResponse(
                status_code=403,
                content={"detail": "Missing X-RapidAPI-Proxy-Secret"},
            )

        # Tráfico autenticado como RapidAPI → aplicar whitelist del Hub
        from_rapid = provided == secret
        if from_rapid and settings.rapidapi_hub_only and not is_hub_allowed(request.method, path):
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Endpoint not available on RapidAPI Hub listing",
                    "path": path,
                },
            )

        return await call_next(request)
