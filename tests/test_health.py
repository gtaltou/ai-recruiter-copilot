import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


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
