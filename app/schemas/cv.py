from typing import Optional

from pydantic import BaseModel, Field


class Competence(BaseModel):
	nom: str
	niveau: Optional[str] = None  # débutant, intermédiaire, expert
	annees_experience: Optional[float] = None


class Experience(BaseModel):
	titre: str
	entreprise: str
	date_debut: str
	date_fin: Optional[str] = None
	description: Optional[str] = None
	competences_acquises: list[str] = Field(default_factory=list)


class Formation(BaseModel):
	diplome: str
	etablissement: str
	annee: str
	domaine: Optional[str] = None


class CV(BaseModel):
	nom: str
	prenom: str
	email: str
	telephone: Optional[str] = None
	titre_poste: Optional[str] = None
	resume: Optional[str] = None
	competences: list[Competence] = Field(default_factory=list)
	experiences: list[Experience] = Field(default_factory=list)
	formations: list[Formation] = Field(default_factory=list)
	langues: list[str] = Field(default_factory=list)
	centres_interet: list[str] = Field(default_factory=list)
