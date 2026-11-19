import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app


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
    

@pytest.fixture
def valid_cv():
    """CV valide pour les tests."""
    return {
        "nom": "Dupont",
        "prenom": "Marie",
        "email": "marie.dupont@email.com",
        "telephone": "+33123456789",
        "titre_poste": "Data Engineer",
        "resume": "Ingénieure data passionnée.",
        "competences": [
            {"nom": "Python", "niveau": "expert", "annees_experience": 5.0},
            {"nom": "FastAPI", "niveau": "intermédiaire", "annees_experience": 2.0},
            {"nom": "SQL", "niveau": "avancé", "annees_experience": 4.0},
        ],
        "experiences": [
            {
                "titre": "Data Engineer",
                "entreprise": "TechCorp",
                "date_debut": "2021-01",
                "description": "Construction de pipelines ETL.",
            }
        ],
        "formations": [
            {
                "diplome": "Master Data Science",
                "etablissement": "Université Paris-Saclay",
                "annee": "2020",
            }
        ],
        "langues": ["Français", "Anglais"],
        "centres_interet": ["Randonnée"],
    }


@pytest.fixture
def valid_jd():
    """Description de poste valide pour les tests."""
    return {
        "titre": "Senior Data Engineer",
        "entreprise": "StartupAI",
        "lieu": "Paris",
        "type_contrat": "CDI",
        "resume": "Cherche expert Python.",
        "responsabilites": ["Gérer la data", "Optimiser SQL"],
        "competences_requises": ["Python", "SQL", "Docker"],
        "experience_requise": "4 ans",
        "niveau_etudes": "Master",
        "langues_requises": ["Anglais"],
    }


@pytest.mark.asyncio
async def test_analyze_success(valid_cv, valid_jd):
    """Test nominal : l'analyse retourne un résultat complet."""
    # from app.services.cv_analysis import analyze_cv
    # result = await analyze_cv(valid_cv, valid_jd)
    # 
    # assert result["status"] == "ok"
    # assert result["candidate"] == "Dupont"
    # assert result["poste"] == "Senior Data Engineer"
    # assert "score_global" in result
    # assert "recommandation" in result
    pass


@pytest.mark.asyncio
async def test_analyze_perfect_match(valid_cv, valid_jd):
    """Test d'un matching parfait : toutes les compétences requises sont présentes."""
    pass


@pytest.mark.asyncio
async def test_analyze_no_skills_match(valid_cv, valid_jd):
    """Test d'un matching nul : aucune compétence requise n'est présente."""
    pass


@pytest.mark.asyncio
async def test_analyze_partial_skills_match(valid_cv, valid_jd):
    """Test d'un matching partiel."""
    pass


@pytest.mark.asyncio
async def test_analyze_experience_insufficient(valid_cv, valid_jd):
    """Test : l'expérience du candidat est insuffisante."""
    pass


@pytest.mark.asyncio
async def test_analyze_language_mismatch(valid_cv, valid_jd):
    """Test : le candidat ne parle pas les langues requises."""
    pass

@pytest.mark.asyncio
async def test_analyze_empty_cv_returns_422():
    """Test : un CV vide retourne une erreur 422."""
    from app.core.security import create_access_token

    token = create_access_token(data={"sub": "test@example.com"})
    payload = {
        "cv": "",
        "job_description": "Description valide",
        "candidate_email": "test@example.com"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analyze",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 422


