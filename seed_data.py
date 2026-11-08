from app.db import SessionLocal
from app.db.models import Analysis
from datetime import datetime, timezone

def seed():
    with SessionLocal() as session:
        analyses = [
            Analysis(
                cv_filename="john_doe_cv.pdf",
                job_title="Data Scientist",
                score=85,
                created_at=datetime.now(timezone.utc),
            ),
            Analysis(
                cv_filename="jane_smith_cv.pdf",
                job_title="Software Engineer",
                score=72,
                created_at=datetime.now(timezone.utc),
            ),
            Analysis(
                cv_filename="bob_johnson_cv.pdf",
                job_title="Product Manager",
                score=91,
                created_at=datetime.now(timezone.utc),
            ),
        ]
        session.add_all(analyses)
        session.commit()
        print("✅ 3 analyses de test ajoutées !")

seed()
