# tests/test_web.py
"""Tests pour les routes web du dashboard."""
import pytest


class TestWebRoutes:
    """Tests des routes web."""

    @pytest.mark.asyncio
    async def test_index_page(self, client):
        """La page d'accueil doit retourner 200."""
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_index_page_content(self, client):
        """La page d'accueil doit contenir le titre attendu."""
        response = await client.get("/")
        assert response.status_code == 200
        content = response.text.lower()
        assert any(word in content for word in ["recruiter", "copilot", "dashboard", "ai"])
