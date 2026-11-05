"""Tests pour les schémas JobDescription."""

import pytest
from pydantic import ValidationError
from app.schemas.job_description import JobDescription


class TestJobDescriptionSchema:
    """Tests de validation du schéma JobDescription."""

    VALID_JD = {
        "titre": "Ingénieur IA",
        "entreprise": "TechCorp",
        "lieu": "Paris",
        "type_contrat": "CDI",
        "resume": "Poste orienté NLP et déploiement de modèles.",
        "responsabilites": ["Développement", "Maintenance"],
        "competences_requises": ["Python", "FastAPI"],
        "competences_souhaitees": ["Docker"],
        "experience_requise": "3 ans",
        "niveau_etudes": "Bac+5",
        "langues_requises": ["Français", "Anglais"],
        "salaire": "60k-70k",
    }

    def test_jd_minimal_valide(self):
        """Seuls 'titre' et 'entreprise' sont requis."""
        jd = JobDescription(titre="Dev", entreprise="Startup")
        assert jd.titre == "Dev"
        assert jd.entreprise == "Startup"
        assert jd.lieu is None
        assert jd.responsabilites == []

    def test_jd_complet_valide(self):
        """Une fiche de poste complète doit être valide."""
        jd = JobDescription(**self.VALID_JD)
        assert jd.titre == "Ingénieur IA"
        assert jd.langues_requises == ["Français", "Anglais"]

    def test_jd_champs_obligatoires(self):
        """Vérifie que 'titre' et 'entreprise' sont obligatoires."""
        with pytest.raises(ValidationError):
            JobDescription(entreprise="Sans Titre")
        with pytest.raises(ValidationError):
            JobDescription(titre="Sans Entreprise")

    def test_jd_valeurs_par_defaut(self):
        """Vérifie que les listes sont vides par défaut et les chaînes à None."""
        jd = JobDescription(titre="Test", entreprise="Test")
        assert jd.responsabilites == []
        assert jd.competences_requises == []
        assert jd.competences_souhaitees == []
        assert jd.langues_requises == []
        assert jd.lieu is None
        assert jd.resume is None

    def test_jd_types_invalides(self):
        """Vérifie la validation des types pour les listes."""
        data = self.VALID_JD.copy()
        data["responsabilites"] = "Ne pas être une liste"
        with pytest.raises(ValidationError):
            JobDescription(**data)

    def test_jd_model_dump(self):
        """Vérifie la sérialisation."""
        jd = JobDescription(**self.VALID_JD)
        d = jd.model_dump()
        assert d["titre"] == "Ingénieur IA"
        assert d["entreprise"] == "TechCorp"
        assert d["lieu"] == "Paris"
        assert isinstance(d["responsabilites"], list)
