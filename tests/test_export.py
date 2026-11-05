import pytest
import pytest_asyncio          # ← ajout
import time
import jwt
from fastapi import status
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

WRONG_JWT_SECRET = "x" * 64   # ≥ 32 octets pour HS256 → pas de warning


@pytest.fixture
def auth_headers():
    payload = {
        "sub": "test-user",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def expired_token_headers():
    payload = {
        "sub": "test-user",
        "exp": int(time.time()) - 3600,
        "iat": int(time.time()) - 7200,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def invalid_token_headers():
    payload = {
        "sub": "test-user",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    token = jwt.encode(payload, WRONG_JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}



@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac



# ── Auth tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_csv_no_token(client):
    r = await client.get("/api/v1/export/csv")
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_export_csv_invalid_token(client, invalid_token_headers):
    r = await client.get("/api/v1/export/csv", headers=invalid_token_headers)
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_export_csv_expired_token(client, expired_token_headers):
    r = await client.get("/api/v1/export/csv", headers=expired_token_headers)
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_export_json_no_token(client):
    r = await client.get("/api/v1/export/json")
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_export_json_invalid_token(client, invalid_token_headers):
    r = await client.get("/api/v1/export/json", headers=invalid_token_headers)
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_export_json_expired_token(client, expired_token_headers):
    r = await client.get("/api/v1/export/json", headers=expired_token_headers)
    assert r.status_code == status.HTTP_403_FORBIDDEN


# ── CSV tests ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_csv_success(client, auth_headers):
    r = await client.get("/api/v1/export/csv", headers=auth_headers)
    assert r.status_code == status.HTTP_200_OK
    assert "text/csv" in r.headers.get("content-type", "")
    assert "attachment" in r.headers.get("content-disposition", "").lower()


@pytest.mark.asyncio
async def test_export_csv_content(client, auth_headers):
    r = await client.get("/api/v1/export/csv", headers=auth_headers)
    lines = r.text.strip().split("\n")
    assert len(lines) >= 1
    header = lines[0].lower().strip()
    # The actual CSV columns from the endpoint
    assert "candidate" in header
    assert "job_title" in header
    assert "match_score" in header


@pytest.mark.asyncio
async def test_export_csv_post(client, auth_headers):
    r = await client.post("/api/v1/export/csv", headers=auth_headers)
    assert r.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ── JSON tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_json_success(client, auth_headers):
    r = await client.get("/api/v1/export/json", headers=auth_headers)
    assert r.status_code == status.HTTP_200_OK
    assert "application/json" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_export_json_content(client, auth_headers):
    r = await client.get("/api/v1/export/json", headers=auth_headers)
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for item in data:
        assert isinstance(item, dict)
        # The actual JSON keys from the endpoint
        assert any(key in item for key in ("candidate", "job_title", "match_score"))


@pytest.mark.asyncio
async def test_export_json_post(client, auth_headers):
    r = await client.post("/api/v1/export/json", headers=auth_headers)
    assert r.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
