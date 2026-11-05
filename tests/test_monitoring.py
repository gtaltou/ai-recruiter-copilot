import pytest
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint returns 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_metrics_middleware_header():
    """Test that the metrics middleware adds the process time header."""
    response = client.get("/api/v1/health")
    assert "X-Process-Time" in response.headers


def test_logging_structured_format(caplog):
    """Vérifie que les logs structurés contiennent les props de requête."""
    client.get("/api/v1/health")

    for record in caplog.records:
        if hasattr(record, "props"):
            assert "method" in record.props
            assert record.props["method"] == "GET"


@pytest.mark.asyncio
async def test_health_endpoint_services():
    """
    Vérifie que le endpoint de santé retourne tous les services
    avec leur statut correct.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:

        response = await ac.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    # Vérifications existantes
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"

    # VÉRIFICATIONS MANQUANTES (lignes 15-16 de health.py)
    assert "services" in data
    assert isinstance(data["services"], dict)
    assert data["services"]["api"] == "up"
    assert data["services"]["database"] == "connected"
    assert len(data["services"]) == 2
