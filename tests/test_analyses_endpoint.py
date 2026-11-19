import pytest
from fastapi import status
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app


pytestmark = pytest.mark.asyncio


class TestAnalysesEndpoint:
    """Tests d'intégration pour les endpoints /api/v1/analyses."""

    async def test_list_analyses_structure(self, client, auth_headers):
        """Vérifie que GET /analyses retourne une structure paginée."""
        response = await client.get("/api/v1/analyses", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data
        assert isinstance(data["items"], list)
        assert "total" in data
        assert "page" in data
        assert "size" in data

    async def test_list_analyses_pagination(self, client, auth_headers):
        """Vérifie les paramètres de pagination."""
        response = await client.get(
            "/api/v1/analyses?page=1&size=5", headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5

    async def test_get_analysis_not_found(self, client, auth_headers):
        """Vérifie qu'un UUID inexistant retourne 404."""
        response = await client.get(
            "/api/v1/analyses/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_analysis_invalid_uuid(self, client, auth_headers):
        """L'endpoint ne valide pas le format UUID → retourne 404."""
        response = await client.get(
            "/api/v1/analyses/pas-un-uuid", headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_analysis_missing_score(self, client, auth_headers):
        """L'endpoint crée l'analyse avec score=0.0 par défaut."""
        response = await client.post(
            "/api/v1/analyses",
            json={
                "candidate_name": "Alice Dupont",
                "cv_text": "Développeuse Python avec 5 ans d'expérience.",
                "job_description": "Nous cherchons un développeur Python.",
            },
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["score"] == 0.0

    async def test_create_analysis_unauthorized(self, client):
        """Vérifie que POST sans token retourne 403."""
        response = await client.post(
            "/api/v1/analyses",
            json={
                "candidate_name": "Bob",
                "cv_text": "test",
                "job_description": "test",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_analysis_method_not_allowed(self, client, auth_headers):
        """PUT n'est pas implémenté → retourne 405."""
        response = await client.put(
            "/api/v1/analyses/00000000-0000-0000-0000-000000000000",
            json={"score": 85},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    async def test_delete_analysis_not_found(self, client, auth_headers):
        """Vérifie que DELETE sur un UUID inexistant retourne 404."""
        response = await client.delete(
            "/api/v1/analyses/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_upload_cv_invalid_pdf(self, client, auth_headers):
        """L'upload d'un PDF invalide retourne 400."""
        response = await client.post(
            "/api/v1/analyses/upload",
            files={"file": ("cv.pdf", b"ceci n'est pas un pdf", "application/pdf")},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_upload_cv_without_file(self, client, auth_headers):
        """Vérifie qu'un upload sans fichier retourne 422."""
        response = await client.post(
            "/api/v1/analyses/upload",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
"""Tests supplémentaires pour app/api/v1/endpoints/analyses.py"""



@pytest.mark.asyncio
class TestAnalysesEndpoint:
    async def test_create_analysis_basic(self, client, auth_headers):
        payload = {
            "cv_filename": "test_cv.pdf",
            "job_title": "Data Engineer",
            "candidate_name": "Marie Dupont",
            "cv_text": "Python FastAPI SQL",
        }
        resp = await client.post("/api/v1/analyses", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["job_title"] == "Data Engineer"
        assert data["cv_filename"] == "test_cv.pdf"
        assert data["status"] == "pending"

    async def test_create_analysis_default_filename(self, client, auth_headers):
        payload = {"cv_text": "Python"}
        resp = await client.post("/api/v1/analyses", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["cv_filename"].startswith("cv_")

    async def test_list_analyses_pagination(self, client, auth_headers):
        resp = await client.get("/api/v1/analyses?page=1&size=5", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["size"] == 5

    async def test_list_analyses_filter_by_status(self, client, auth_headers):
        resp = await client.get("/api/v1/analyses?status=completed", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["status"] == "completed"

    async def test_list_analyses_filter_by_min_score(self, client, auth_headers):
        resp = await client.get("/api/v1/analyses?min_score=50", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            if item["score"] is not None:
                assert item["score"] >= 50

    async def test_list_analyses_sort_by_score_desc(self, client, auth_headers):
        resp = await client.get("/api/v1/analyses?sort_by=score&order=desc", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        scores = [item["score"] for item in data["items"] if item["score"] is not None]
        assert scores == sorted(scores, reverse=True)

    async def test_get_analysis_not_found(self, client, auth_headers):
        resp = await client.get("/api/v1/analyses/non-existent-id", headers=auth_headers)
        assert resp.status_code == 404
        assert "Analyse introuvable" in resp.json()["detail"]

    async def test_delete_analysis_not_found(self, client, auth_headers):
        resp = await client.delete("/api/v1/analyses/non-existent-id", headers=auth_headers)
        assert resp.status_code == 404

    async def test_ranking_endpoint(self, client, auth_headers):
        resp = await client.get("/api/v1/analyses/ranking", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "ranking" in data
        assert "total" in data
        # Vérifie que le classement est trié par score décroissant
        scores = [r["score"] for r in data["ranking"] if r["score"] is not None]
        assert scores == sorted(scores, reverse=True)

    async def test_ranking_with_filters(self, client, auth_headers):
        resp = await client.get(
            "/api/v1/analyses/ranking?status=completed&min_score=50&limit=10",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["ranking"]) <= 10

    async def test_export_csv(self, client, auth_headers):
        resp = await client.get("/api/v1/analyses/export/csv", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert "filename=analyses.csv" in resp.headers["content-disposition"]

    async def test_export_csv_with_filters(self, client, auth_headers):
        resp = await client.get(
            "/api/v1/analyses/export/csv?status=completed&min_score=50",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    @patch("app.api.v1.endpoints.analyses.notify_async")
    @patch("app.api.v1.endpoints.analyses.manager.broadcast", new_callable=AsyncMock)
    async def test_analyze_cv_triggers_notifications(
        self, mock_broadcast, mock_notify, client, auth_headers
    ):
        # Créer une analyse d'abord
        create_resp = await client.post(
            "/api/v1/analyses",
            json={"cv_text": "Python FastAPI SQL Docker"},
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        analysis_id = create_resp.json()["id"]

        # Lancer l'analyse
        resp = await client.post(f"/api/v1/analyses/{analysis_id}/analyze", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["score"] is not None
      
