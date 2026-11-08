import time
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

import jwt
from app.core.security import security_settings

metrics_logger = logging.getLogger("app.metrics")


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        elapsed = time.time() - start_time
        response.headers["X-Process-Time"] = str(elapsed)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = logging.getLogger("app.metrics")
        logger.info(f"Request: {request.method} {request.url.path}")
        start_time = time.time()
        response = await call_next(request)
        elapsed = time.time() - start_time
        logger.info(f"Response: {response.status_code} ({elapsed:.3f}s)")
        return response


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Middleware JWT : lit le token depuis le header Authorization ou le cookie access_token."""

    EXEMPT_PATHS = {
        "/web/login",
        "/login",
        "/dev-token",
        "/health",
        "/health_check",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path

        if path.startswith("/web") or path.startswith("/static") or path.startswith("/templates"):
            return await call_next(request)

        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            token = request.cookies.get("access_token")

        if token:
            try:
                jwt.decode(
                    token,
                    security_settings.jwt_secret_key,
                    algorithms=[security_settings.jwt_algorithm],
                )
                return await call_next(request)
            except jwt.ExpiredSignatureError:
                return JSONResponse(status_code=401, content={"detail": "Token expired"})
            except jwt.InvalidTokenError:
                return JSONResponse(status_code=403, content={"detail": "Invalid token"})

        return JSONResponse(status_code=403, content={"detail": "Not authenticated"})
