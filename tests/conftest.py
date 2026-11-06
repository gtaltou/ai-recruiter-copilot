"""Fixtures partagées pour toute la suite de tests."""
import os
import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["SECRET_KEY"] = "x" * 76

from app.core.config import settings
from app.core.security import security_settings
from app.main import app

# Source unique du secret JWT
TEST_JWT_SECRET = settings.JWT_SECRET


# ---------------------------------------------------------------------------
# JWT : clé longue pour éviter InsecureKeyLengthWarning
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _long_jwt_secret(monkeypatch):
    """Remplace le secret JWT par settings.JWT_SECRET pendant chaque test."""
    monkeypatch.setattr(security_settings, "jwt_secret_key", TEST_JWT_SECRET)


@pytest.fixture
def expired_token_headers():
    """Token déjà expiré → 403."""
    payload = {
        "sub": "test-user",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def auth_headers():
    """Token JWT valide et non expiré."""
    now = int(time.time())
    token = jwt.encode(
        {"sub": "test-user", "iat": now, "exp": now + 3600},
        TEST_JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Client HTTP asynchrone
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client():
    """Client HTTP branché sur l'app FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Données de test
# ---------------------------------------------------------------------------
@pytest.fixture
def valid_cv() -> dict:
    return {
        "nom": "Dupont",
        "prenom": "Marie",
        "email": "marie.dupont@email.com",
        "telephone": "+33123456789",
        "titre_poste": "Data Engineer",
        "poste_actuel": "Data Engineer",
        "resume": "Ingénieure data passionnée.",
        "competences": ["Python", "FastAPI", "SQL"],
        "annees_experience": 5.0,
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
def valid_jd() -> dict:
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
