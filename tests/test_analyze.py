import jwt
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import security_settings


@pytest.mark.asyncio
async def test_analyze_endpoint():
    """Test que l'endpoint /analyze accepte les données conformes aux schémas."""
    # Générer un token JWT valide pour le test
    token = jwt.encode(
        {"sub": "test-user", "exp": 9999999999},
        security_settings.jwt_secret_key,
        algorithm=security_settings.jwt_algorithm,
    )
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cv_payload = {
            "nom": "Dupont",
            "prenom": "Marie",
            "email": "marie.dupont@email.com",
            "telephone": "+33123456789",
            "titre_poste": "Data Engineer",
            "resume": "Ingénieure data passionnée.",
            "competences": [
                {"nom": "Python", "niveau": "expert", "annees_experience": 5.0},
                {"nom": "FastAPI", "niveau": "intermédiaire", "annees_experience": 2.0}
            ],
            "experiences": [
                {
                    "titre": "Data Engineer",
                    "entreprise": "TechCorp",
                    "date_debut": "2021-01",
                    "description": "Construction de pipelines ETL."
                }
            ],
            "formations": [
                {
                    "diplome": "Master Data Science",
                    "etablissement": "Université Paris-Saclay",
                    "annee": "2020"
                }
            ],
            "langues": ["Français", "Anglais"],
            "centres_interet": ["Randonnée"]
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
            "langues_requises": ["Anglais"]
        }
        
        response = await client.post(
            "/api/v1/analyze", 
            json={"cv": cv_payload, "job_description": jd_payload}, 
            headers=headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["candidate"] == "Dupont"
    assert data["poste"] == "Senior Data Engineer"
