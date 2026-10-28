from app.core.llm import llm_client
from app.schemas.cv import CV
from app.schemas.job_description import JobDescription
import logging

logger = logging.getLogger(__name__)

EVALUATION_SYSTEM_PROMPT = """Tu es un recruteur technique senior spécialisé en évaluation de candidats.

Analyse le CV par rapport à la description de poste et génère un rapport structuré.

Réponds UNIQUEMENT avec un JSON valide :
{
    "note_globale": <int 0-100>,
    "competences_techniques": {"note": <int>, "details": "..."},
    "experience": {"note": <int>, "details": "..."},
    "soft_skills_estimes": {"note": <int>, "details": "..."},
    "adhesion_culturelle": {"note": <int>, "details": "..."},
    "forces": ["force1", "force2"],
    "axes_amelioration": ["axe1", "axe2"],
    "recommandation": <"fort_recommandé" | "recommandé" | "réserve" | "déconseillé">,
    "questions_entretien": ["question1", "question2", "question3"],
    "synthese": "résumé concis de l'évaluation"
}"""

class EvaluationAgent:
    """Agent qui produit une évaluation détaillée."""

    async def evaluate(self, cv: CV, jd: JobDescription, match_result: dict) -> dict:
        """Évalue un candidat et génère un rapport."""
        prompt = self._build_prompt(cv, jd, match_result)
        return await llm_client.generate_structured(
            system_prompt=EVALUATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=dict,
        )

    def _build_prompt(self, cv: CV, jd: JobDescription, match: dict) -> str:
        return f"""CV :
Nom : {cv.nom_complet}
Expérience : {cv.annees_experience} ans
Compétences : {', '.join(cv.competences)}
Diplôme : {cv.diplome_le_plus_eleve}

Poste :
Titre : {jd.titre}
Compétences requises : {', '.join(jd.competences_requises)}
Expérience requise : {jd.experience_requise} ans

Analyse préliminaire :
Score match : {match.get('score_match', 'N/A')}/100
Compétences présentes : {match.get('competences_requises', [])}
Compétences manquantes : {match.get('competences_manquantes', [])}"""
