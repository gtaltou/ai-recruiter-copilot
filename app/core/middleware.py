from __future__ import annotations

import logging
import re
import time
from typing import Any
from urllib.parse import parse_qs

import jwt
from starlette.authentication import AuthenticationError
from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.security import rate_limiter, security_settings

logger = logging.getLogger(__name__)

EXEMPT_PATHS: set[str] = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/dashboard",
    "/api/v1/health",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
}

EXEMPT_PREFIXES: tuple[str, ...] = (
    "/web/",
    "/static/",
    "/templates/",
)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware qui log chaque requête et sa durée."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "%s %s -> %d (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware qui collecte des métriques basiques (requêtes, statuts, latence)."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.request_count = 0
        self.status_counts: dict[int, int] = {}
        self.total_latency = 0.0

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        self.request_count += 1
        start = time.time()
        response = await call_next(request)
        latency = time.time() - start
        self.total_latency += latency
        self.status_counts[response.status_code] = (
            self.status_counts.get(response.status_code, 0) + 1
        )
        response.headers["X-Process-Time"] = f"{latency * 1000:.1f}"
        return response



class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Middleware JWT qui protège les routes de l'API."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.secret_key = security_settings.jwt_secret_key
        self.algorithm = security_settings.jwt_algorithm

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        path = request.url.path.rstrip("/") or "/"

        # Vérifier si la route est exemptée
        if path in EXEMPT_PATHS or any(
            path.startswith(prefix) for prefix in EXEMPT_PREFIXES
        ):
            return await call_next(request)

        # Extraire le token
        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if not token:
            return JSONResponse(
                status_code=403,
                content={"detail": "Not authenticated"},
            )

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            request.state.user = payload
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=403,
                content={"detail": "Token expired"},
            )
        except jwt.PyJWTError:
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid token"},
            )

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting par IP."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        if not rate_limiter.check(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )
        return await call_next(request)
