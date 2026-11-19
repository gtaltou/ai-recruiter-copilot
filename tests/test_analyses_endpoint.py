import pytest
from fastapi import status

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
