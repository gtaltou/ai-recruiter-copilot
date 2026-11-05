"""Fixtures partagées pour toute la suite de tests."""
# en haut de tests/conftest.py, AVANT d'importer app.*
import os
os.environ["SECRET_KEY"] = "x" * 76

import pytest
import pytest_asyncio
import jwt
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.security import security_settings

from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings

#TEST_JWT_SECRET = settings.JWT_SECRET  # ou le bon nom d'attribut


@pytest.fixture
def expired_token_headers():
    """Token déjà expiré → 403."""
    payload = {
        "sub": "test-user",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}



# ---------------------------------------------------------------------------
# JWT : clé longue pour éviter InsecureKeyLengthWarning
# (HS256 exige >= 32 octets, HS512 >= 64 octets)
# ---------------------------------------------------------------------------
#TEST_JWT_SECRET = "test-secret-" + "x" * 64  # 76 octets


@pytest.fixture(autouse=True)
def _long_jwt_secret(monkeypatch):
    """Remplace le secret JWT par une version longue pendant chaque test."""
    monkeypatch.setattr(security_settings, "jwt_secret_key", TEST_JWT_SECRET)


# ---------------------------------------------------------------------------
# Client HTTP asynchrone
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client():
    """Client HTTP branché sur l'app FastAPI (équivalent httpx.AsyncClient)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


''' @pytest.fixture
def auth_headers(_long_jwt_secret):
    """En-têtes d'authentification avec un token JWT valide et non expiré."""
    token = jwt.encode(
        {"sub": "test-user", "exp": 9999999999},
        security_settings.jwt_secret_key,
        algorithm=security_settings.jwt_algorithm,
    )
    return {"Authorization": f"Bearer {token}"} '''
    
    
import time
from app.core.config import settings

TEST_JWT_SECRET = settings.JWT_SECRET  # source unique de vérité

@pytest_asyncio.fixture
def auth_headers():
    now = int(time.time())
    token = jwt.encode(
        {"sub": "test-user", "iat": now, "exp": now + 3600},
        TEST_JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Données de test (fixtures = retour d'une copie fraîche à chaque test)
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
            "competences": ["Python", "FastAPI", "SQL"],   # list[str] et non list[dict]
            "annees_experience": 5.0,                      # champ requis à la racine
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
    
    
    

    
 