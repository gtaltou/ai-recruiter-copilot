from app.rag.vector_store import vector_store
from app.core.llm import llm_client
from app.schemas.cv import CV
from app.schemas.job_description import JobDescription
import logging

logger = logging.getLogger(__name__)

SOURCING_SYSTEM_PROMPT = """Tu es un expert en sourcing technique. Ton rôle est d'analyser un CV 
par rapport à une description de poste et de fournir une évaluation détaillée du match.

Réponds UNIQUEMENT avec un JSON valide contenant :
{
    "score_match": <int 0-100>,
    "competences_requises": ["liste des compétences requises présentes"],
    "competences_manquantes": ["liste des compétences requises absentes"],
    "annees_experience": <nombre d'années>,
    "niveau_poste": <"junior" | "confirmé" | "senior" | "expert">,
    "commentaire": "analyse concise du profil"
}"""

class SourcingAgent:
    """Agent responsable du sourcing et matching CV ↔ JD."""

    async def find_candidates(self, jd: JobDescription, top_k: int = 10) -> list[dict]:
        """Recherche les meilleurs candidats via RAG."""
        return vector_store.search(
            query=f"{jd.titre} {jd.description} {', '.join(jd.competences_requises)}",
            n_results=top_k,
        )

    async def evaluate_match(self, cv: CV, jd: JobDescription) -> dict:
        """Évalue le fit entre un CV et une JD via LLM."""
        prompt = f"""CV CANDIDAT :
{self._format_cv(cv)}

DESCRIPTION DE POSTE :
{self._format_jd(jd)}"""

        result = await llm_client.generate_structured(
            system_prompt=SOURCING_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=dict,
        )
        return result

    def _format_cv(self, cv: CV) -> str:
        return f"""Nom : {cv.nom_complet}
Email : {cv.email}
Expérience : {cv.annees_experience} ans
Compétences : {', '.join(cv.competences)}
Diplôme : {cv.diplome_le_plus_eleve}
Expériences : {cv.experiences_professionnelles}"""

    def _format_jd(self, jd: JobDescription) -> str:
        return f"""Titre : {jd.titre}
Description : {jd.description}
Compétences requises : {', '.join(jd.competences_requises)}
Expérience requise : {jd.experience_requise} ans
Localisation : {jd.localisation}"""
