"""Tests pour le module app.core.config."""
import pytest
from app.core.config import settings


class TestSettings:
    """Tests pour la configuration de l'application."""

    def test_app_name_exists(self):
        """Vérifie que APP_NAME est défini."""
        assert hasattr(settings, "APP_NAME")
        assert isinstance(settings.APP_NAME, str)
        assert len(settings.APP_NAME) > 0

    def test_environment_exists(self):
        """Vérifie que ENVIRONMENT est défini."""
        assert hasattr(settings, "ENVIRONMENT")
        assert settings.ENVIRONMENT in ("development", "staging", "production", "test")

    def test_log_level_exists(self):
        """Vérifie que LOG_LEVEL est défini."""
        assert hasattr(settings, "LOG_LEVEL")
        assert settings.LOG_LEVEL in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    def test_log_json_exists(self):
        """Vérifie que LOG_JSON est un booléen."""
        assert hasattr(settings, "LOG_JSON")
        assert isinstance(settings.LOG_JSON, bool)

    def test_database_url_exists(self):
        """Vérifie que DATABASE_URL est défini (si applicable)."""
        # Ne pas échouer si le champ n'existe pas
        if hasattr(settings, "DATABASE_URL"):
            assert isinstance(settings.DATABASE_URL, str)

    def test_debug_mode_consistent(self):
        """Vérifie la cohérence DEBUG / ENVIRONMENT."""
        if hasattr(settings, "DEBUG"):
            if settings.ENVIRONMENT == "production":
                assert settings.DEBUG is False
            else:
                assert isinstance(settings.DEBUG, bool)

    def test_settings_are_immutable(self):
        """Vérifie que les settings sont en lecture seule (pydantic BaseSettings)."""
        with pytest.raises((TypeError, ValueError)):
            settings.APP_NAME = "Hacked"
