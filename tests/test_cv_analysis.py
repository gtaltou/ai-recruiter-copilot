"""Tests de l'endpoint /api/v1/analyze."""

import pytest

# Fixtures partagées (définies dans tests/conftest.py) :
#   client, auth_headers, expired_token_headers, valid_cv, valid_jd


# --- Tests d'authentification ---

@pytest.mark.asyncio
async def test_analyze_success(client, auth_headers, valid_cv, valid_jd):
    """Requête valide → 200 OK."""
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": valid_cv, "job_description": valid_jd},
        headers=auth_headers,
    )
    print(response.json())   # garde le print pour voir le detail du 403

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_analyze_no_token(client, valid_cv, valid_jd):
    """Sans token → 403 Forbidden."""
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": valid_cv, "job_description": valid_jd},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_analyze_invalid_token(client, valid_cv, valid_jd):
    """Token invalide (mauvaise signature) → 403 Forbidden."""
    headers = {"Authorization": "Bearer invalidtoken123"}
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": valid_cv, "job_description": valid_jd},
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_analyze_expired_token(client, expired_token_headers, valid_cv, valid_jd):
    """Token expiré → 403 Forbidden."""
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": valid_cv, "job_description": valid_jd},
        headers=expired_token_headers,
    )
    assert response.status_code == 403


# --- Tests de validation des données ---

@pytest.mark.asyncio
async def test_analyze_empty_body(client, auth_headers):
    """Corps vide → 422 Unprocessable Entity."""
    response = await client.post("/api/v1/analyze", json={}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_missing_fields(client, auth_headers):
    """Payload sans 'cv' ni 'job_description' → 422."""
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": None, "job_description": None},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_empty_cv(client, auth_headers, valid_jd):
    """CV vide → 422."""
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": {}, "job_description": valid_jd},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_invalid_email(client, auth_headers, valid_cv, valid_jd):
    """Email invalide → 422."""
    invalid_cv = {**valid_cv, "email": "pas-un-email"}
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": invalid_cv, "job_description": valid_jd},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_negative_experience(client, auth_headers, valid_cv, valid_jd):
    """Années d'expérience négatives → 422."""
    invalid_cv = {**valid_cv, "annees_experience": -5}
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": invalid_cv, "job_description": valid_jd},
        headers=auth_headers,
    )
    assert response.status_code == 422


# --- Tests de protocole HTTP ---

@pytest.mark.asyncio
async def test_analyze_get_method(client, auth_headers):
    """GET (au lieu de POST) → 405 Method Not Allowed."""
    response = await client.get("/api/v1/analyze", headers=auth_headers)
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_analyze_wrong_content_type(client, auth_headers):
    """Content-Type texte (pas JSON) → 415 ou 422."""
    response = await client.post(
        "/api/v1/analyze",
        content="cv=hello",
        headers={**auth_headers, "Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code in (415, 422)
