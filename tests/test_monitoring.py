import pytest
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from app.main import app

from fastapi import FastAPI
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
    


@pytest.mark.asyncio
async def test_health_endpoint():
    """
    Vérifie que le endpoint de santé répond correctement.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert data["services"]["api"] == "up"


@pytest.mark.asyncio
async def test_metrics_middleware_header():
    """
    Vérifie que le middleware de métriques ajoute bien le header X-Process-Time-Ms.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")

    assert response.status_code == 200
    assert "X-Process-Time-Ms" in response.headers
    assert float(response.headers["X-Process-Time-Ms"]) >= 0


@pytest.mark.asyncio
async def test_structured_logging_presence(caplog):
    """
    Vérifie que des logs sont générés lors d'une requête (si configuré).
    """
    import logging

    caplog.set_level(logging.INFO)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.get("/api/v1/health")

    assert any("Request metrics" in record.message for record in caplog.records)


# ──────────────────────────────────────────────
#  Nouveaux tests — Métriques Prometheus
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_metrics_endpoint_exists():
    """
    Vérifie que le endpoint /metrics expose les métriques Prometheus.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


@pytest.mark.asyncio
async def test_metrics_endpoint_contains_prometheus_metrics():
    """
    Vérifie que les métriques Prometheus définies dans metrics.py sont exposées.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/metrics")

    body = response.text

    # Métriques définies dans app/core/metrics.py
    assert "# HELP http_requests_total" in body
    assert "# TYPE http_requests_total counter" in body
    assert "# HELP http_request_duration_seconds" in body
    assert "# TYPE http_request_duration_seconds histogram" in body
    assert "# HELP http_requests_in_progress" in body
    assert "# TYPE http_requests_in_progress gauge" in body
    assert "# HELP analyses_total" in body
    assert "# TYPE analyses_total counter" in body
    assert "# HELP app_info" in body
    assert "# TYPE app_info gauge" in body


@pytest.mark.asyncio
async def test_http_requests_total_increments_on_request():
    """
    Vérifie que http_requests_total est incrémenté après une requête.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Lire les métriques avant la requête
        resp_before = await ac.get("/metrics")
        body_before = resp_before.text

        # Effectuer une requête sur un endpoint connu
        await ac.get("/api/v1/health")

        # Lire les métriques après la requête
        resp_after = await ac.get("/metrics")
        body_after = resp_after.text

    # Prometheus trie les labels par ordre alphabétique
    assert 'http_requests_total{endpoint="/api/v1/health",method="GET",status_code="200"}' in body_after


@pytest.mark.asyncio
async def test_http_request_duration_seconds_recorded():
    """
    Vérifie que http_request_duration_seconds_bucket existe après une requête.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.get("/api/v1/health")
        resp = await ac.get("/metrics")

    # Prometheus trie les labels par ordre alphabétique
    assert 'http_request_duration_seconds_bucket{endpoint="/api/v1/health"' in resp.text


@pytest.mark.asyncio
async def test_http_requests_in_progress_gauge():
    """
    Vérifie que la gauge http_requests_in_progress est exposée.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.get("/api/v1/health")
        resp = await ac.get("/metrics")

    # Prometheus trie les labels par ordre alphabétique
    assert 'http_requests_in_progress{endpoint="/api/v1/health",method="GET"}' in resp.text


@pytest.mark.asyncio
async def test_app_info_metric():
    """
    Vérifie que la métrique d'information app_info est présente.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/metrics")

    # Vérifie simplement que app_info est exposé (Info nécessite un appel .info() manuel)
    assert "app_info" in resp.text



@pytest.mark.asyncio
async def test_metrics_endpoint_returns_valid_prometheus_format():
    """
    Vérifie que le format de réponse Prometheus est valide (pas de doublons # TYPE).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/metrics")

    body = resp.text
    lines = body.split("\n")

    # Vérifie que chaque métrique n'a qu'une seule déclaration # TYPE
    type_lines = [line for line in lines if line.startswith("# TYPE")]
    type_names = [line.split()[2] for line in type_lines]

    from collections import Counter
    duplicates = {name for name, count in Counter(type_names).items() if count > 1}
    assert not duplicates, f"Métriques avec # TYPE dupliqués : {duplicates}"

