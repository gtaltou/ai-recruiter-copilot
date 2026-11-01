from pydantic import BaseModel, EmailStr, Field

class CV(BaseModel):
    nom: str
    email: EmailStr
    telephone: str
    competences: list[str]
    annees_experience: int = Field(ge=0)
    poste_actuel: str
