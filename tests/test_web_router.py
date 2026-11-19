import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_index_returns_html(client):
    """GET / — page d'accueil retourne du HTML."""
    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_login_page_returns_html(client):
    """GET /login — page de login retourne du HTML."""
    response = await client.get("/login")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_login_post_invalid_token(client):
    """POST /login — token invalide → 401."""
    response = await client.post("/login", data={"token": "invalid_token"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_dashboard_redirects_without_auth(client):
    """GET /dashboard — sans cookie → 303."""
    response = await client.get("/dashboard", follow_redirects=False)
    print(f"\n[DEBUG] Status: {response.status_code}")
    print(f"[DEBUG] Headers: {dict(response.headers)}")
    print(f"[DEBUG] URL finale: {response.url}")
    assert response.status_code == status.HTTP_303_SEE_OTHER



@pytest.mark.asyncio
async def test_dashboard_with_auth(client, auth_headers):
    """GET /dashboard — avec auth → page HTML."""
    # On utilise le token Bearer pour générer un cookie valide
    token = auth_headers["Authorization"].replace("Bearer ", "")
    client.cookies.set("access_token", token)
    response = await client.get("/dashboard")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_logout(client):
    """POST /logout — déconnexion → redirection."""
    response = await client.post("/logout", follow_redirects=False)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers.get("location") == "/login"


@pytest.mark.asyncio
async def test_dev_token(client):
    """GET /dev-token — génération de token de développement."""
    response = await client.get("/dev-token")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_api_stats_without_auth(client):
    """GET /api/stats — sans cookie → 303."""
    response = await client.get("/api/stats", follow_redirects=False)
    assert response.status_code == status.HTTP_303_SEE_OTHER
