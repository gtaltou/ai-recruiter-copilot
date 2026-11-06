# tests/test_db_models.py
"""Tests pour les modèles SQLAlchemy et la persistance."""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.db.models import Analysis


class TestAnalysisModel:
    """Tests du modèle Analysis."""

    @pytest.fixture
    def db_session(self):
        """Fixture avec base SQLite in-memory isolée."""
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    def test_create_analysis(self, db_session):
        """Créer et récupérer une analyse complète."""
        analysis = Analysis(
            cv_filename="cv_dupont.pdf",
            job_title="Développeur Python",
            score=87.5,
            status="completed",
            result_json='{"match": 87.5, "skills": ["Python", "FastAPI"]}',
        )
        db_session.add(analysis)
        db_session.commit()

        saved = db_session.query(Analysis).first()
        assert saved is not None
        assert saved.cv_filename == "cv_dupont.pdf"
        assert saved.job_title == "Développeur Python"
        assert saved.score == 87.5
        assert saved.status == "completed"
        assert saved.id is not None

    def test_default_status(self, db_session):
        """Le statut par défaut doit être 'completed'."""
        analysis = Analysis(
            cv_filename="cv_test.pdf",
            job_title="Développeur",
            score=50.0,
        )
        db_session.add(analysis)
        db_session.commit()

        saved = db_session.query(Analysis).first()
        assert saved.status == "completed"

    def test_created_at_is_set_automatically(self, db_session):
        """created_at doit être renseigné automatiquement."""
        analysis = Analysis(
            cv_filename="cv.pdf",
            job_title="Ingénieur",
            score=50.0,
        )
        db_session.add(analysis)
        db_session.commit()

        saved = db_session.query(Analysis).first()
        assert saved.created_at is not None
        assert isinstance(saved.created_at, datetime)

    def test_multiple_analyses(self, db_session):
        """Insertion et comptage de plusieurs analyses."""
        analyses = [
            Analysis(
                cv_filename=f"cv_{i}.pdf",
                job_title=f"Poste {i}",
                score=i * 10.0,
            )
            for i in range(3)
        ]
        for a in analyses:
            db_session.add(a)
        db_session.commit()

        assert db_session.query(Analysis).count() == 3

    def test_query_by_status(self, db_session):
        """Filtrage par statut."""
        db_session.add_all(
            [
                Analysis(
                    cv_filename="cv1.pdf",
                    job_title="Poste 1",
                    score=80.0,
                    status="completed",
                ),
                Analysis(
                    cv_filename="cv2.pdf",
                    job_title="Poste 2",
                    score=50.0,
                    status="completed",
                ),
            ]
        )
        db_session.commit()

        completed = db_session.query(Analysis).filter(Analysis.status == "completed").all()
        assert len(completed) == 2

    def test_update_analysis(self, db_session):
        """Mise à jour d'un champ existant."""
        analysis = Analysis(
            cv_filename="v1.pdf",
            job_title="Poste",
            score=70.0,
            status="completed",
        )
        db_session.add(analysis)
        db_session.commit()

        analysis.status = "completed"
        analysis.score = 95.0
        db_session.commit()

        updated = db_session.query(Analysis).first()
        assert updated.status == "completed"
        assert updated.score == 95.0

    def test_delete_analysis(self, db_session):
        """Suppression d'une analyse."""
        analysis = Analysis(
            cv_filename="a_supprimer.pdf",
            job_title="Poste",
            score=30.0,
        )
        db_session.add(analysis)
        db_session.commit()

        db_session.delete(analysis)
        db_session.commit()

        assert db_session.query(Analysis).count() == 0


class TestGetDb:
    """Tests de la fonction get_db()."""

    def test_get_db_yields_session(self):
        """get_db() doit produire une session SQLAlchemy."""
        gen = get_db()
        db = next(gen)
        assert db is not None
        import os
        if os.path.exists("ai_recruiter.db"):
            os.remove("ai_recruiter.db")
        with pytest.raises(StopIteration):
            next(gen)

    def test_get_db_closes_session_on_exit(self):
        """La session doit être fermée après le bloc try/finally."""
        gen = get_db()
        db = next(gen)
        with pytest.raises(StopIteration):
            next(gen)
        import os
        if os.path.exists("ai_recruiter.db"):
            os.remove("ai_recruiter.db")
