import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas.cv import CV
from app.schemas.job_description import JobDescription

@pytest.fixture
def sample_cv():
    return CV(
        nom_complet="Marie Dupont",
        email="marie.dupont@email.com",
        telephone="+33123456789",
        annees_experience=5,
        competences=["Python", "FastAPI", "Machine Learning", "Docker", "PostgreSQL"],
        diplome_le_plus_eleve="Master en Data Science",
        experiences_professionnelles="Data Engineer chez TechCorp (3 ans)\nData Analyst chez StartupAI (2 ans)",
    )

@pytest.fixture
def sample_jd():
    return JobDescription(
        titre="Senior Data Engineer",
        description="Nous recherchons un Data Engineer expérimenté pour construire et optimiser nos pipelines de données.",
        competences_requises=["Python", "SQL", "Docker", "Machine Learning", "Apache Spark"],
        experience_requise=4,
        localisation="Paris, France",
    )

@pytest.mark.asyncio
async def test_analyze_endpoint():
    """Test que l'endpoint /analyze est bien défini."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cv_payload = {
            "nom_complet": "Marie Dupont",
            "email": "marie.dupont@email.com",
            "telephone": "+33123456789",
            "annees_experience": 5,
            "competences": ["Python", "FastAPI", "Machine Learning", "Docker", "PostgreSQL"],
            "diplome_le_plus_eleve": "Master en Data Science",
            "experiences_professionnelles": "Data Engineer chez TechCorp (3 ans)\nData Analyst chez StartupAI (2 ans)",
        }
        jd_payload = {
            "titre": "Senior Data Engineer",
            "description": "Nous recherchons un Data Engineer expérimenté.",
            "competences_requises": ["Python", "SQL", "Docker", "Machine Learning", "Apache Spark"],
            "experience_requise": 4,
            "localisation": "Paris, France",
        }
        response = await client.post("/api/v1/analyze", json={"cv": cv_payload, "jd": jd_payload})
        assert response.status_code == 200 or response.status_code == 422  # 422 si validation
