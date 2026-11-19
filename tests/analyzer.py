"""Tests pour app/services/analyzer.py — 100 % de couverture."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.analyzer import (
    analyze_cv_job_match,
    calculate_score,
    generate_recommendation,
    extract_skills_from_cv,
    extract_skills_from_jd,
    match_skills,
    get_analysis_result,
)


class TestExtractSkills:
    """Couverture lignes 31-34, 39-55."""

    def test_extract_skills_from_cv_with_list(self):
        """CV avec compétences structurées (liste de dicts)."""
        cv = {
            "competences": [
                {"nom": "Python", "niveau": "expert", "annees_experience": 5},
                {"nom": "FastAPI", "niveau": "intermédiaire", "annees_experience": 2},
            ]
        }
        result = extract_skills_from_cv(cv)
        assert result == ["Python", "FastAPI"]

    def test_extract_skills_from_cv_with_strings(self):
        """CV avec compétences en liste de chaînes."""
        cv = {"competences": ["Python", "FastAPI", "Docker"]}
        result = extract_skills_from_cv(cv)
        assert result == ["Python", "FastAPI", "Docker"]

    def test_extract_skills_from_cv_empty(self):
        """CV sans compétences."""
        cv = {"competences": []}
        result = extract_skills_from_cv(cv)
        assert result == []

    def test_extract_skills_from_cv_missing_key(self):
        """CV sans clé 'competences'."""
        cv = {"nom": "Jean"}
        result = extract_skills_from_cv(cv)
        assert result == []

    def test_extract_skills_from_jd_with_list(self):
        """JD avec compétences requises."""
        jd = {"competences_requises": ["Python", "SQL", "Docker"]}
        result = extract_skills_from_jd(jd)
        assert result == ["Python", "SQL", "Docker"]

    def test_extract_skills_from_jd_empty(self):
        """JD sans compétences."""
        jd = {"competences_requises": []}
        result = extract_skills_from_jd(jd)
        assert result == []

    def test_extract_skills_from_jd_missing_key(self):
        """JD sans clé 'competences_requises'."""
        jd = {"titre": "Dev"}
        result = extract_skills_from_jd(jd)
        assert result == []


class TestMatchSkills:
    """Couverture lignes 69-137."""

    def test_match_skills_perfect(self):
        """Correspondance parfaite."""
        cv_skills = ["Python", "FastAPI", "Docker"]
        jd_skills = ["Python", "FastAPI", "Docker"]
        matched, missing, rate = match_skills(cv_skills, jd_skills)
        assert matched == ["Python", "FastAPI", "Docker"]
        assert missing == []
        assert rate == 100.0

    def test_match_skills_partial(self):
        """Correspondance partielle."""
        cv_skills = ["Python", "FastAPI"]
        jd_skills = ["Python", "SQL", "Docker"]
        matched, missing, rate = match_skills(cv_skills, jd_skills)
        assert matched == ["Python"]
        assert missing == ["SQL", "Docker"]
        assert rate == pytest.approx(33.33, rel=0.01)

    def test_match_skills_no_match(self):
        """Aucune correspondance."""
        cv_skills = ["Java"]
        jd_skills = ["Python", "SQL"]
        matched, missing, rate = match_skills(cv_skills, jd_skills)
        assert matched == []
        assert missing == ["Python", "SQL"]
        assert rate == 0.0

    def test_match_skills_empty_jd(self):
        """JD sans compétences → 100 %."""
        cv_skills = ["Python"]
        jd_skills = []
        matched, missing, rate = match_skills(cv_skills, jd_skills)
        assert matched == []
        assert missing == []
        assert rate == 100.0

    def test_match_skills_case_insensitive(self):
        """Insensible à la casse."""
        cv_skills = ["python"]
        jd_skills = ["Python"]
        matched, missing, rate = match_skills(cv_skills, jd_skills)
        assert matched == ["python"]
        assert rate == 100.0

    def test_match_skills_empty_cv(self):
        """CV sans compétences."""
        cv_skills = []
        jd_skills = ["Python"]
        matched, missing, rate = match_skills(cv_skills, jd_skills)
        assert matched == []
        assert missing == ["Python"]
        assert rate == 0.0


class TestCalculateScore:
    """Couverture des calculs de score."""

    def test_calculate_score_perfect(self):
        """Score parfait (100 % compétences, expérience suffisante)."""
        score = calculate_score(
            skills_match_rate=100.0,
            cv_experience=5,
            jd_experience_required=3,
        )
        assert score == 100.0

    def test_calculate_score_partial(self):
        """Score partiel."""
        score = calculate_score(
            skills_match_rate=50.0,
            cv_experience=2,
            jd_experience_required=5,
        )
        assert 0 < score < 100

    def test_calculate_score_zero(self):
        """Score nul."""
        score = calculate_score(
            skills_match_rate=0.0,
            cv_experience=0,
            jd_experience_required=5,
        )
        assert score == 0.0


class TestGenerateRecommendation:
    """Couverture lignes 151-178."""

    def test_recommendation_convoke(self):
        """Score ≥ 75 → 'À convoquer'."""
        rec = generate_recommendation(85.0)
        assert rec == "À convoquer"

    def test_recommendation_reserve(self):
        """Score entre 50 et 74 → 'En réserve'."""
        rec = generate_recommendation(60.0)
        assert rec == "En réserve"

    def test_recommendation_reject(self):
        """Score < 50 → 'Refuser'."""
        rec = generate_recommendation(30.0)
        assert rec == "Refuser"

    def test_recommendation_boundary_75(self):
        """Limite haute → 'À convoquer'."""
        rec = generate_recommendation(75.0)
        assert rec == "À convoquer"

    def test_recommendation_boundary_50(self):
        """Limite basse → 'En réserve'."""
        rec = generate_recommendation(50.0)
        assert rec == "En réserve"


@pytest.mark.asyncio
class TestAnalyzeCvJobMatch:
    """Tests d'intégration avec mock LLM."""

    @patch("app.services.analyzer.llm_client")
    async def test_analyze_success(self, mock_llm):
        """Analyse complète avec LLM mocké."""
        mock_llm.generate_structured = AsyncMock(return_value={
            "score_global": 85.0,
            "recommandation": "À convoquer",
            "forces": ["Python avancé"],
            "faiblesses": ["Pas de Docker"],
        })

        result = await analyze_cv_job_match(
            cv={"nom": "Jean", "competences": [{"nom": "Python", "niveau": "expert", "annees_experience": 5}]},
            job_description={"titre": "Dev", "competences_requises": ["Python", "Docker"]},
        )

        assert result["score_global"] == 85.0
        assert result["recommandation"] == "À convoquer"

    @patch("app.services.analyzer.llm_client")
    async def test_analyze_llm_error(self, mock_llm):
        """Erreur LLM → fallback sur calcul local."""
        mock_llm.generate_structured = AsyncMock(side_effect=Exception("API Error"))

        result = await analyze_cv_job_match(
            cv={"nom": "Jean", "competences": [{"nom": "Python", "niveau": "expert", "annees_experience": 5}]},
            job_description={"titre": "Dev", "competences_requises": ["Python"]},
        )

        assert "score_global" in result
        assert result["recommandation"] in ("À convoquer", "En réserve", "Refuser")

    @patch("app.services.analyzer.llm_client")
    async def test_analyze_empty_cv(self, mock_llm):
        """CV vide → géré sans erreur."""
        mock_llm.generate_structured = AsyncMock(return_value={
            "score_global": 0.0,
            "recommandation": "Refuser",
            "forces": [],
            "faiblesses": ["CV vide"],
        })

        result = await analyze_cv_job_match(
            cv={},
            job_description={"titre": "Dev", "competences_requises": ["Python"]},
        )
        assert result["score_global"] == 0.0


class TestGetAnalysisResult:
    """Fonction utilitaire get_analysis_result."""

    def test_get_analysis_result_full(self):
        """Structure complète."""
        result = get_analysis_result(
            candidate="Dupont",
            poste="Dev",
            score=85.0,
            recommandation="À convoquer",
            matched_skills=["Python"],
            missing_skills=["Docker"],
            experience_years=5,
            details={"forces": ["Python"], "faiblesses": ["Docker"]},
        )
        assert result["candidate"] == "Dupont"
        assert result["poste"] == "Dev"
        assert result["score_global"] == 85.0
        assert result["recommandation"] == "À convoquer"
        assert result["competences"]["correspondantes"] == ["Python"]
        assert result["competences"]["manquantes"] == ["Docker"]

    def test_get_analysis_result_minimal(self):
        """Structure minimale."""
        result = get_analysis_result(
            candidate="Jean",
            poste="Ingénieur",
            score=50.0,
            recommandation="En réserve",
            matched_skills=[],
            missing_skills=[],
            experience_years=0,
            details=None,
        )
        assert result["candidate"] == "Jean"
        assert result["details"] is None
