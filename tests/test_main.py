"""Tests pour le module main : vérifie le bon déroulement du lifespan."""
import pytest
import sqlalchemy as sa


@pytest.mark.asyncio
async def test_lifespan_creates_tables():
    """Exécute le contexte lifespan directement et vérifie la création des tables."""
    from app.main import lifespan, app
    from app.db import engine

    # Déclenche le startup (setup_logging + create_all)
    async with lifespan(app):
        pass

    # Vérifie que la table 'analyses' existe
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()
    assert "analyses" in tables
