"""Tests pour le middleware de métriques."""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from httpx import AsyncClient, ASGITransport
import time
import logging

from app.core.metrics import MetricsMiddleware


@pytest.fixture
def app() -> FastAPI:
    """Crée une application FastAPI de test avec le middleware MetricsMiddleware."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "ok"}

    @app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(0.05)
        return {"status": "slow"}

    @app.post("/create")
    async def create_endpoint():
        return {"created": True}

    @app.get("/error")
    async def error_endpoint():
        return JSONResponse(status_code=500, content={"error": "server_error"})

    app.add_middleware(MetricsMiddleware)
    return app


@pytest.fixture
def client(app: FastAPI) -> AsyncClient:
    """Crée un client HTTP asynchrone de test."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_metrics_middleware_adds_process_time_header(client: AsyncClient):
    """Vérifie que le middleware ajoute le header X-Process-Time-Ms."""
    response = await client.get("/test")
    assert response.status_code == 200
    assert "X-Process-Time-Ms" in response.headers
    value = float(response.headers["X-Process-Time-Ms"])
    assert value > 0
    assert value < 1000  # Raisonnable pour un endpoint simple


@pytest.mark.asyncio
async def test_metrics_middleware_header_format(client: AsyncClient):
    """Vérifie que le header X-Process-Time-Ms est un float valide avec 2 décimales."""
    response = await client.get("/test")
    header_value = response.headers["X-Process-Time-Ms"]
    # Vérifie que c'est un float avec au plus 2 décimales
    parts = header_value.split(".")
    assert len(parts) == 2
    assert len(parts[1]) <= 2


@pytest.mark.asyncio
@patch("app.core.metrics.logger")
async def test_metrics_middleware_logs_correctly(mock_logger: MagicMock, app: FastAPI):
    """Vérifie que le logger est appelé avec les bons paramètres."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/test")
        mock_logger.info.assert_called_once()
        args, kwargs = mock_logger.info.call_args
        assert args[0] == "Request metrics"
        extra = kwargs.get("extra", {})
        assert extra["metric_type"] == "http_request"
        assert extra["method"] == "GET"
        assert extra["path"] == "/test"
        assert extra["status_code"] == 200
        assert "latency_ms" in extra
        assert extra["latency_ms"] > 0


@pytest.mark.asyncio
async def test_metrics_middleware_works_with_post(client: AsyncClient):
    """Vérifie que le middleware fonctionne avec les requêtes POST."""
    response = await client.post("/create", json={"key": "value"})
    assert response.status_code == 200
    assert "X-Process-Time-Ms" in response.headers
    assert float(response.headers["X-Process-Time-Ms"]) > 0


@pytest.mark.asyncio
async def test_metrics_middleware_tracks_slow_requests(app: FastAPI):
    """Vérifie que les requêtes lentes sont correctement mesurées."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/slow")
        assert response.status_code == 200
        process_time = float(response.headers["X-Process-Time-Ms"])
        # La latence doit être significativement > 0 (au moins 30ms pour un sleep de 50ms)
        assert process_time >= 30, f"La latence ({process_time}ms) est trop basse pour un endpoint avec 50ms de délai"



@pytest.mark.asyncio
async def test_metrics_middleware_with_error_response(client: AsyncClient):
    """Vérifie que le middleware gère correctement les réponses d'erreur."""
    response = await client.get("/error")
    assert response.status_code == 500
    assert "X-Process-Time-Ms" in response.headers
    assert float(response.headers["X-Process-Time-Ms"]) > 0


@pytest.mark.asyncio
async def test_metrics_middleware_tracks_status_code(client: AsyncClient):
    """Vérifie que le middleware rapporte le bon status code pour les erreurs."""
    # Route qui n'existe pas → 404
    response = await client.get("/nonexistent")
    assert response.status_code == 404
    assert "X-Process-Time-Ms" in response.headers


@pytest.mark.asyncio
async def test_metrics_middleware_latency_increases_with_delay(app: FastAPI):
    """Vérifie que la latence mesurée augmente avec un délai artificiel."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response_fast = await client.get("/test")
        fast_time = float(response_fast.headers["X-Process-Time-Ms"])

        response_slow = await client.get("/slow")
        slow_time = float(response_slow.headers["X-Process-Time-Ms"])

        # La requête lente doit être au moins 20ms plus longue que la rapide
        difference = slow_time - fast_time
        assert difference >= 20, f"La différence ({difference}ms) est insuffisante, attendu >= 20ms"


@pytest.mark.asyncio
async def test_metrics_middleware_does_not_alter_response_body(client: AsyncClient):
    """Vérifie que le middleware ne modifie pas le corps de la réponse."""
    response = await client.get("/test")
    assert response.json() == {"message": "ok"}


@pytest.mark.asyncio
async def test_metrics_middleware_works_with_concurrent_requests(app: FastAPI):
    """Vérifie que le middleware gère les requêtes concurrentes."""
    import asyncio
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async def make_request():
            resp = await client.get("/test")
            return float(resp.headers["X-Process-Time-Ms"])

        results = await asyncio.gather(*[make_request() for _ in range(5)])
        assert all(r > 0 for r in results)
        assert len(results) == 5
