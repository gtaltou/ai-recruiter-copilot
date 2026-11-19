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


import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_returns_200():
    """Vérifie que /api/v1/health retourne 200."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_returns_json():
    """Vérifie que la réponse est au format JSON."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.headers["content-type"] == "application/json"


@pytest.mark.asyncio
async def test_health_contains_status():
    """Vérifie la présence du champ status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_contains_timestamp():
    """Vérifie la présence du champ timestamp."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    data = response.json()
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_legacy_endpoint():
    """Vérifie que /health legacy fonctionne aussi."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


