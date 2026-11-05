"""Tests de charge (load/stress) pour AI Recruiter Copilot avec Locust."""

import random
from datetime import datetime, timedelta

import jwt
from locust import HttpUser, task, between, tag

from app.core.config import settings

# Données de test valides (conformes aux schémas Pydantic)
VALID_CV = {
    "nom": "Jean Dupont",
    "email": "jean.dupont@example.com",
    "telephone": "+33612345678",
    "competences": ["Python", "FastAPI", "Docker", "PostgreSQL"],
    "annees_experience": 5,
    "poste_actuel": "Développeur Backend",
}

VALID_JD = {
    "titre": "Développeur Backend Senior",
    "entreprise": "TechCorp",
    "description": "Développement d'APIs REST avec Python et FastAPI.",
    "competences_requises": ["Python", "FastAPI", "Docker"],
    "niveau_experience": "Senior",
    "type_contrat": "CDI",
}


def _generate_token() -> str:
    """Génère un token JWT valide signé avec JWT_SECRET."""
    payload = {
        "sub": "test-user",
        "email": "test@example.com",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


class RecruiterCopilotUser(HttpUser):
    """Simule un utilisateur interagissant avec l'API."""

    wait_time = between(0.5, 3.0)

    def on_start(self):
        """Génère un token valide au démarrage de chaque utilisateur."""
        self.token = _generate_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @tag("analyze")
    @task(5)
    def analyze_endpoint(self):
        """Charge test du endpoint /api/v1/analyze (poids: 5)."""
        payload = {"cv": VALID_CV, "job_description": VALID_JD}
        with self.client.post(
            "/api/v1/analyze",
            json=payload,
            headers=self.headers,
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code in (403, 422):
                resp.failure(f"Statut inattendu: {resp.status_code}")
            else:
                resp.failure(f"Erreur serveur: {resp.status_code}")

    @tag("export_csv")
    @task(3)
    def export_csv_endpoint(self):
        """Charge test du endpoint /api/v1/export/csv (poids: 3)."""
        params = {
            "candidat": "Jean Dupont",
            "job_title": "Développeur Backend Senior",
            "match_score": 85.5,
        }
        with self.client.get(
            "/api/v1/export/csv",
            params=params,
            headers=self.headers,
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                if "text/csv" in resp.headers.get("content-type", ""):
                    resp.success()
                else:
                    resp.failure(f"Type incorrect: {resp.headers.get('content-type')}")
            elif resp.status_code == 403:
                resp.failure(f"Auth échouée: {resp.status_code}")
            else:
                resp.failure(f"Erreur: {resp.status_code}")

    @tag("export_json")
    @task(3)
    def export_json_endpoint(self):
        """Charge test du endpoint /api/v1/export/json (poids: 3)."""
        params = {
            "candidat": "Jean Dupont",
            "job_title": "Développeur Backend Senior",
            "match_score": 85.5,
        }
        with self.client.get(
            "/api/v1/export/json",
            params=params,
            headers=self.headers,
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                if "application/json" in resp.headers.get("content-type", ""):
                    resp.success()
                else:
                    resp.failure(f"Type incorrect: {resp.headers.get('content-type')}")
            elif resp.status_code == 403:
                resp.failure(f"Auth échouée: {resp.status_code}")
            else:
                resp.failure(f"Erreur: {resp.status_code}")

    @tag("stress_concurrent")
    @task(1)
    def stress_burst_analyze(self):
        """Envoie 3 requêtes analyze en rafale (poids: 1)."""
        payload = {"cv": VALID_CV, "job_description": VALID_JD}
        for i in range(3):
            with self.client.post(
                "/api/v1/analyze",
                json=payload,
                headers=self.headers,
                catch_response=True,
                name="/api/v1/analyze [burst]",
            ) as resp:
                if resp.status_code == 200:
                    resp.success()
                else:
                    resp.failure(f"Burst #{i} échoué: {resp.status_code}")

    @tag("invalid_auth")
    @task(1)
    def invalid_auth_request(self):
        """Test de charge sans authentification valide (poids: 1)."""
        payload = {"cv": VALID_CV, "job_description": VALID_JD}
        with self.client.post(
            "/api/v1/analyze",
            json=payload,
            headers={"Authorization": "Bearer token-invalide"},
            catch_response=True,
            name="/api/v1/analyze [no auth]",
        ) as resp:
            if resp.status_code == 403:
                resp.success()
            else:
                resp.failure(f"Devrait retourner 403, reçu {resp.status_code}")
