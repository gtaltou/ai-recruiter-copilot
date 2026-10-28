from app.core.llm import llm_client
import logging

logger = logging.getLogger(__name__)

REPORT_SYSTEM_PROMPT = """Tu es un expert en rédaction de rapports de recrutement.

À partir des données d'évaluation, génère un rapport final professionnel et actionnable.

Réponds UNIQUEMENT avec un JSON valide :
{
    "resume_executif": "résumé en 2-3 phrases",
    "analyse_detaillee": {
        "competences_techniques": "...",
        "experience_professionnelle": "...",
        "soft_skills": "...",
        "adhesion_culturelle": "..."
    },
    "recommandation_finale": "...",
    "prochaines_etapes": ["étape1", "étape2"],
    "risques": ["risque1", "risque2"],
    "date_evaluation": "YYYY-MM-DD"
}"""

class ReportAgent:
    """Agent qui synthétise l'évaluation en rapport final."""

    async def generate_report(
        self, match_result: dict, evaluation_result: dict
    ) -> dict:
        """Génère le rapport final structuré."""
        prompt = f"""Données du matching :
Score : {match_result.get('score_match')}/100
Commentaire : {match_result.get('commentaire')}

Données de l'évaluation :
Note globale : {evaluation_result.get('note_globale')}/100
Forces : {evaluation_result.get('forces')}
Axes d'amélioration : {evaluation_result.get('axes_amelioration')}
Recommandation : {evaluation_result.get('recommandation')}
Synthèse : {evaluation_result.get('synthese')}"""

        return await llm_client.generate_structured(
            system_prompt=REPORT_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=dict,
        )

    def format_for_api(self, report: dict, cv_id: str, jd_id: str) -> dict:
        """Formate le rapport pour la réponse API."""
        return {
            "cv_id": cv_id,
            "jd_id": jd_id,
            "resume_executif": report["resume_executif"],
            "analyse_detaillee": report["analyse_detaillee"],
            "recommandation_finale": report["recommandation_finale"],
            "prochaines_etapes": report["prochaines_etapes"],
            "risques": report["risques"],
            "date_evaluation": report["date_evaluation"],
        }
