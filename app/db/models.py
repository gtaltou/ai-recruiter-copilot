import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, Text
from app.db import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cv_filename = Column(String, nullable=False)
    job_title = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    status = Column(String, default="completed")
    result_json = Column(Text, nullable=True)  # stockage du résultat complet en JSON
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
