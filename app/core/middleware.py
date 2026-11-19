"""Middleware ASGI pour le logging structuré et l'authentification JWT."""

import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings
import logging
logger = logging.getLogger(__name__)

# Routes publiques qui ne nécessitent pas de token JWT
PUBLIC_ROUTES = {
    "/api/v1/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/docs",
    # Routes web
    "/",
    "/login",
    "/logout",
    "/dashboard",
    "/dev-token",
    "/api/stats",
    # Métriques Prometheus
    "/metrics",
}



# ──────────────────────────────────────────────
#  Dataclasses de contexte
# ──────────────────────────────────────────────

@dataclass
class RequestLogContext:
    """Contexte de logging pour une requête HTTP."""
    method: str = ""
    path: str = ""
    query: str = ""
    request_id: str = ""
    body_preview: str = ""


@dataclass
class ResponseLogContext:
    """Contexte de logging pour une réponse HTTP."""
    status_code: int = 0
    elapsed_ms: float = 0.0
    request_id: str = ""


# ──────────────────────────────────────────────
#  StructuredLoggingMiddleware (style Starlette)
#  Ajoute un X-Request-ID et logue les requêtes
# ──────────────────────────────────────────────

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Log structuré de chaque requête HTTP."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # Injecter request_id dans le state pour traçabilité interne
        request.state.request_id = request_id

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            logger.error(
                "Request failed",
                extra={
                    "props": {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "query": str(request.query_params),
                        "elapsed_ms": round(elapsed * 1000, 2),
                        "status_code": 500,
                        "error": str(exc),
                    }
                },
            )
            raise

        elapsed = time.perf_counter() - start_time

        # Log si erreur (>=400) ou si DEBUG est activé
        should_log = (
            response.status_code >= 400
            or logger.isEnabledFor(logging.DEBUG)
        )

        if should_log:
            level = logger.error if response.status_code >= 500 else logger.warning
            level(
                f"{request.method} {request.url.path} -> {response.status_code}",
                extra={
                    "props": {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "elapsed_ms": round(elapsed * 1000, 2),
                    }
                },
            )

        response.headers["X-Request-ID"] = request_id
        return response


# ──────────────────────────────────────────────
#  LoggingMiddleware (ASGI natif + dispatch)
#  Logue chaque requête/réponse de façon simple
# ──────────────────────────────────────────────

class LoggingMiddleware:
    """Middleware ASGI qui logue chaque requête/réponse."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        method = scope.get("method", "")
        path = scope.get("path", "")

        async def _send(message):
            if message["type"] == "http.response.start":
                elapsed = (time.perf_counter() - start) * 1000
                status = message.get("status", 0)
                logger.info(
                    "%s %s -> %d (%.1f ms)",
                    method,
                    path,
                    status,
                    elapsed,
                )
            await send(message)

        await self.app(scope, receive, _send)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Méthode de compatibilité pour les tests unitaires."""
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %d (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response


# ──────────────────────────────────────────────
#  JWTAuthMiddleware (ASGI natif + dispatch)
#  Protège les routes par JWT
# ──────────────────────────────────────────────

class JWTAuthMiddleware:
    """Middleware ASGI qui protège les routes par JWT."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in PUBLIC_ROUTES:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()

        if not auth_header.startswith("Bearer "):
            response = JSONResponse(
                status_code=403,
                content={"detail": "Authentication required"},
            )
            await self._send_response(scope, receive, send, response)
            return

        token = auth_header[7:]
        try:
            jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            response = JSONResponse(
                status_code=403,
                content={"detail": "Token has expired"},
            )
            await self._send_response(scope, receive, send, response)
            return
        except jwt.InvalidTokenError:
            response = JSONResponse(
                status_code=403,
                content={"detail": "Invalid token"},
            )
            await self._send_response(scope, receive, send, response)
            return

        await self.app(scope, receive, send)

    async def _send_response(
        self, scope: Scope, receive: Receive, send: Send, response: JSONResponse
    ) -> None:
        """Envoie une réponse JSON directement via le protocole ASGI."""
        await response(scope, receive, send)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Méthode de compatibilité pour les tests unitaires."""
        path = request.url.path

        if path in PUBLIC_ROUTES:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=403,
                content={"detail": "Authentication required"},
            )

        token = auth_header[7:]
        try:
            jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=403,
                content={"detail": "Token has expired"},
            )
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid token"},
            )

        return await call_next(request)
