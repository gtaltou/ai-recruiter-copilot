import jwt
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


# Données CV valides (conforme au schéma CV)
VALID_CV = {
    "nom": "Jean Dupont",
    "email": "jean.dupont@example.com",
    "telephone": "+33612345678",
    "competences": ["Python", "FastAPI", "Machine Learning", "Docker"],
    "annees_experience": 5,
    "poste_actuel": "Ingénieur IA"
}

VALID_JD = {
    "titre": "Ingénieur IA Senior",
    "entreprise": "TechCorp",
    "lieu": "Paris",
    "type_contrat": "CDI",
    "resume": "Recherche d'un ingénieur IA pour rejoindre notre équipe R&D.",
    "responsabilites": [
        "Développer des modèles de ML",
        "Participer à l'architecture technique",
        "Encadrer des développeurs juniors"
    ],
    "competences_requises": ["Python", "FastAPI", "Machine Learning"],
    "competences_souhaitees": ["Docker", "Kubernetes", "AWS"],
    "experience_requise": "5 ans minimum",
    "niveau_etudes": "Bac+5",
    "langues_requises": ["Français", "Anglais"],
    "salaire": "65-85k€"
}


@pytest.fixture
def auth_headers():
    """Génère un token JWT valide pour les tests."""
    token = jwt.encode(
        {"sub": "test-user", "exp": 9999999999},
        settings.JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def expired_token_headers():
    """Génère un token JWT expiré."""
    token = jwt.encode(
        {"sub": "test-user", "exp": 0},  # exp dans le passé
        settings.JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client():
    """Fixture client HTTP asynchrone."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --- Tests d'authentification ---

@pytest.mark.asyncio
async def test_analyze_success(client, auth_headers):
    """Requête valide → 200 OK."""
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": VALID_CV, "job_description": VALID_JD},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_analyze_no_token(client):
    """Sans token → 403 Forbidden."""
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": VALID_CV, "job_description": VALID_JD},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_analyze_invalid_token(client):
    """Token invalide (mauvaise signature) → 403 Forbidden."""
    headers = {"Authorization": "Bearer invalidtoken123"}
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": VALID_CV, "job_description": VALID_JD},
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_analyze_expired_token(client, expired_token_headers):
    """Token expiré → 403 Forbidden."""
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": VALID_CV, "job_description": VALID_JD},
        headers=expired_token_headers,
    )
    assert response.status_code == 403


# --- Tests de validation des données ---

@pytest.mark.asyncio
async def test_analyze_empty_body(client, auth_headers):
    """Corps vide → 422 Unprocessable Entity."""
    response = await client.post(
        "/api/v1/analyze",
        json={},
        headers=auth_headers,
    )
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
async def test_analyze_empty_cv(client, auth_headers):
    """CV vide → 422."""
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": {}, "job_description": VALID_JD},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_invalid_email(client, auth_headers):
    """Email invalide → 422."""
    invalid_cv = {**VALID_CV, "email": "pas-un-email"}
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": invalid_cv, "job_description": VALID_JD},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_negative_experience(client, auth_headers):
    """Années d'expérience négatives → 422."""
    invalid_cv = {**VALID_CV, "annees_experience": -5}
    response = await client.post(
        "/api/v1/analyze",
        json={"cv": invalid_cv, "job_description": VALID_JD},
        headers=auth_headers,
    )
    assert response.status_code == 422


# --- Tests de protocole HTTP ---

@pytest.mark.asyncio
async def test_analyze_get_method(client, auth_headers):
    """GET (au lieu de POST) → 405 Method Not Allowed."""
    response = await client.get(
        "/api/v1/analyze",
        headers=auth_headers,
    )
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_analyze_wrong_content_type(client, auth_headers):
    """Content-Type texte (pas JSON) → 415 ou 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as raw_client:
        response = await raw_client.post(
            "/api/v1/analyze",
            content="cv=hello",
            headers={
                **auth_headers,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
    assert response.status_code in (415, 422)
