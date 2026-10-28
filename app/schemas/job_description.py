from pydantic import BaseModel, Field
from typing import Optional


class JobDescription(BaseModel):
    titre: str
    entreprise: str
    lieu: Optional[str] = None
    type_contrat: Optional[str] = None  # CDI, CDD, Freelance, etc.
    resume: Optional[str] = None
    responsabilites: list[str] = []
    competences_requises: list[str] = []
    competences_souhaitees: list[str] = []
    experience_requise: Optional[str] = None
    niveau_etudes: Optional[str] = None
    langues_requises: list[str] = []
    salaire: Optional[str] = None
