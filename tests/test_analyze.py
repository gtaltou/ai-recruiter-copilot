import jwt
import pytest
import time
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_analyze_endpoint():
    """Test que l'endpoint /analyze accepte les données conformes aux schémas."""
    token = jwt.encode(
        {"sub": "test-user", "exp": time.time() + 3600},
        settings.JWT_SECRET,
        algorithm="HS256",
    )

    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        cv_payload = {
            "nom": "Dupont",
            "email": "marie.dupont@email.com",
            "telephone": "+33123456789",
            "competences": ["Python", "FastAPI", "SQL"],
            "annees_experience": 5,
            "poste_actuel": "Data Engineer",
        }

        jd_payload = {
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

        response = await client.post(
            "/api/v1/analyze",
            json={"cv": cv_payload, "job_description": jd_payload},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["candidate"] == "Dupont"
    assert data["poste"] == "Senior Data Engineer"
