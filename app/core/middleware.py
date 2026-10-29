from fastapi import Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import security_settings, rate_limiter, verify_jwt_token

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        if not rate_limiter.check(client_ip):
            raise HTTPException(status_code=429, detail="Too many requests. Slow down!")
        return await call_next(request)

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Routes publiques
        public_paths = ["/docs", "/openapi.json", "/redoc", "/health", "/ping", "/api/v1/auth"]
        if any(request.url.path.startswith(p) for p in public_paths):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        return await call_next(request)

def setup_middlewares(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(JWTAuthMiddleware)