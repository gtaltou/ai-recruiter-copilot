"""Tests pour app/core/middleware.py (LoggingMiddleware & JWTAuthMiddleware)."""
import asyncio
import time
import logging
import jwt
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
...

import time
import logging
import jwt
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint

from app.core.middleware import LoggingMiddleware, JWTAuthMiddleware
from app.core.config import settings


# ──────────────────────────────────────────────
# LoggingMiddleware
# ──────────────────────────────────────────────

class TestLoggingMiddleware:
    """Vérifie que chaque requête/réponse est bien loguée."""

    @pytest.mark.asyncio
    async def test_logs_request_and_response(self, caplog):
        """Doit logger la méthode, le path, le status et le temps."""
        caplog.set_level(logging.INFO)
        middleware = LoggingMiddleware(app=MagicMock())

        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/v1/analyze"

        response = MagicMock()
        response.status_code = 200

        async def fake_call_next(_):
            await asyncio.sleep(0.01)  # simule un délai mesurable
            return response

        await middleware.dispatch(request, fake_call_next)

        assert any("POST /api/v1/analyze" in r.message for r in caplog.records)
        assert any("200" in r.message for r in caplog.records)
        assert any("s)" in r.message for r in caplog.records)  # temps écoulé

    @pytest.mark.asyncio
    async def test_logs_error_status(self, caplog):
        """Doit logger correctement un status 500."""
        caplog.set_level(logging.INFO)
        middleware = LoggingMiddleware(app=MagicMock())

        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/v1/export/csv"

        response = MagicMock()
        response.status_code = 500

        async def fake_call_next(_):
            return response

        await middleware.dispatch(request, fake_call_next)

        assert any("500" in r.message for r in caplog.records)


# ──────────────────────────────────────────────
# JWTAuthMiddleware
# ──────────────────────────────────────────────

def _valid_token():
    """Génère un token JWT valide avec les bons paramètres."""
    import time as t
    payload = {"sub": "test_user", "exp": t.time() + 3600}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def _expired_token():
    """Génère un token JWT expiré."""
    import time as t
    payload = {"sub": "test_user", "exp": t.time() - 3600}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


class TestJWTAuthMiddleware:
    """Vérifie la protection des routes par JWT."""

    @pytest.mark.asyncio
    async def test_public_routes_pass_without_token(self):
        """Les routes publiques (health, docs) ne nécessitent pas de token."""
        middleware = JWTAuthMiddleware(app=MagicMock())

        for path in ["/api/v1/health", "/docs", "/openapi.json", "/redoc"]:
            request = MagicMock(spec=Request)
            request.url.path = path
            request.headers = {}

            async def fake_call_next(_):
                return JSONResponse(status_code=200, content={"ok": True})

            response = await middleware.dispatch(request, fake_call_next)
            assert response.status_code == 200, f"Route publique {path} refusée"

    @pytest.mark.asyncio
    async def test_no_auth_header_returns_403(self):
        """Requête sans header Authorization → 403."""
        middleware = JWTAuthMiddleware(app=MagicMock())

        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/analyze"
        request.headers = {}

        async def fake_call_next(_):
            return JSONResponse(status_code=200, content={})

        response = await middleware.dispatch(request, fake_call_next)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_bearer_token_returns_403(self):
        """Token invalide (mauvais format ou mauvais secret) → 403."""
        middleware = JWTAuthMiddleware(app=MagicMock())

        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/analyze"
        request.headers = {"Authorization": "Bearer invalid_jwt_token"}

        async def fake_call_next(_):
            return JSONResponse(status_code=200, content={})

        response = await middleware.dispatch(request, fake_call_next)
        assert response.status_code == 403
        body = response.body.decode()
        assert "Invalid token" in body

    @pytest.mark.asyncio
    async def test_expired_token_returns_403(self):
        """Token expiré → 403 avec message dédié."""
        middleware = JWTAuthMiddleware(app=MagicMock())

        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/analyze"
        request.headers = {"Authorization": f"Bearer {_expired_token()}"}

        async def fake_call_next(_):
            return JSONResponse(status_code=200, content={})

        response = await middleware.dispatch(request, fake_call_next)
        assert response.status_code == 403
        body = response.body.decode()
        assert "expired" in body.lower()

    @pytest.mark.asyncio
    async def test_valid_token_passes(self):
        """Token valide → la requête passe (200)."""
        middleware = JWTAuthMiddleware(app=MagicMock())

        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/analyze"
        request.headers = {"Authorization": f"Bearer {_valid_token()}"}

        async def fake_call_next(_):
            return JSONResponse(status_code=200, content={"result": "ok"})

        response = await middleware.dispatch(request, fake_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_bearer_prefix_returns_403(self):
        """Header sans 'Bearer ' → 403."""
        middleware = JWTAuthMiddleware(app=MagicMock())

        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/analyze"
        request.headers = {"Authorization": _valid_token()}  # pas de "Bearer "

        async def fake_call_next(_):
            return JSONResponse(status_code=200, content={})

        response = await middleware.dispatch(request, fake_call_next)
        assert response.status_code == 403
