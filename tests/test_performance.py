"""Performance / benchmark tests for the AI Recruiter Copilot API."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
import jwt
import time


@pytest.fixture
def valid_token():
    """Generate a valid JWT token for authenticated requests."""
    return jwt.encode(
        {"sub": "test-user", "role": "recruiter"},
        settings.JWT_SECRET,
        algorithm="HS256",
    )


@pytest.fixture
def auth_headers(valid_token):
    """Return headers with a valid Bearer token."""
    return {"Authorization": f"Bearer {valid_token}"}


@pytest.mark.benchmark(min_rounds=10, max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_benchmark_analyze_endpoint(benchmark, auth_headers):
    """Benchmark the /api/v1/analyze endpoint under load."""

    payload = {
        "cv": {
            "nom": "Jean Dupont",
            "email": "jean.dupont@email.com",
            "telephone": "+33612345678",
            "competences": ["Python", "FastAPI", "Machine Learning"],
            "annees_experience": 5,
            "poste_actuel": "Ingénieur logiciel"
        },
        "job_description": {
            "titre": "Développeur Senior",
            "entreprise": "TechCorp",
            "description": "Développement d'applications web avec Python et FastAPI.",
            "competences_requises": ["Python", "FastAPI", "Docker"],
            "annees_experience_requises": 3
        }
    }

    transport = ASGITransport(app=app)

    async def _run():
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/analyze", json=payload, headers=auth_headers)
            return resp.status_code, resp.elapsed.total_seconds()

    # benchmark the async call
    result = await benchmark(_run)
    status_code, elapsed = result
    assert status_code == 200, f"Expected 200, got {status_code}"
    assert elapsed < 5.0, f"Response too slow: {elapsed:.2f}s"


@pytest.mark.benchmark(min_rounds=10, max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_benchmark_export_csv(benchmark, auth_headers):
    """Benchmark the CSV export endpoint."""

    transport = ASGITransport(app=app)

    async def _run():
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/export/csv", headers=auth_headers)
            return resp.status_code, len(resp.content)

    result = await benchmark(_run)
    status_code, content_length = result
    assert status_code == 200, f"Expected 200, got {status_code}"
    assert content_length > 0, "Empty CSV response"


@pytest.mark.benchmark(min_rounds=10, max_time=2.0, warmup=True)
@pytest.mark.asyncio
async def test_benchmark_export_json(benchmark, auth_headers):
    """Benchmark the JSON export endpoint."""

    transport = ASGITransport(app=app)

    async def _run():
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/export/json", headers=auth_headers)
            return resp.status_code, len(resp.content)

    result = await benchmark(_run)
    status_code, content_length = result
    assert status_code == 200, f"Expected 200, got {status_code}"
    assert content_length > 0, "Empty JSON response"


@pytest.mark.benchmark(min_rounds=5, max_time=3.0, warmup=True)
@pytest.mark.asyncio
async def test_benchmark_auth_overhead(benchmark):
    """Benchmark the overhead of JWT auth rejection."""

    headers = {"Authorization": "Bearer invalid-token-12345"}
    payload = {
        "cv": {"nom": "Test", "email": "test@test.com", "telephone": "000", "competences": [], "annees_experience": 0, "poste_actuel": "Test"},
        "job_description": {"titre": "Test", "entreprise": "Test", "description": "Test", "competences_requises": [], "annees_experience_requises": 0}
    }

    transport = ASGITransport(app=app)

    async def _run():
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/analyze", json=payload, headers=headers)
            return resp.status_code

    result = await benchmark(_run)
    status_code = result
    assert status_code == 403, f"Expected 403, got {status_code}"
