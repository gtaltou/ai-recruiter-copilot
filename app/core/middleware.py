import time
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt

from app.core.config import settings

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
    async def dispatch(self, request: Request, call_next):
        # Routes publiques (health, docs)
        if request.url.path in ["/api/v1/health", "/docs", "/openapi.json", "/redoc"] or \
           request.url.path.startswith(("/docs/", "/openapi/")):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=403, content={"detail": "Not authenticated"})

        token = auth_header.split("Bearer ")[1]
        try:
            jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=403, content={"detail": "Token expired"})
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=403, content={"detail": "Invalid token"})

        return await call_next(request)
