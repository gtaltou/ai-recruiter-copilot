from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

import jwt
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseSettings):
    """Security configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jwt_secret_key: str = "super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    allowed_origins: list[str] = ["*"]


security_settings = SecuritySettings()


class RateLimiter:
    """Simple in-memory sliding-window rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def check(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        # Nettoyer les timestamps expirés
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > window_start
        ]

        if len(self.requests[client_ip]) >= self.max_requests:
            return False

        self.requests[client_ip].append(now)
        return True


rate_limiter = RateLimiter(
    max_requests=security_settings.rate_limit_requests,
    window_seconds=security_settings.rate_limit_window_seconds,
)


def verify_jwt_token(token: str) -> dict[str, Any] | None:
    """Vérifie et décode un token JWT. Retourne le payload ou None si invalide."""
    try:
        payload = jwt.decode(
            token,
            security_settings.jwt_secret_key,
            algorithms=[security_settings.jwt_algorithm],
        )
        return payload
    except jwt.PyJWTError:
        return None
