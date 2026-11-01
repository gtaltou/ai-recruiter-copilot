"""Tests pour les schémas CV."""

import pytest
from pydantic import ValidationError
from app.schemas.cv import CV


class TestCVSchema:
    """Tests de validation du schéma CV."""

    VALID_CV = {
        "nom": "Jean Dupont",
        "email": "jean.dupont@email.com",
        "telephone": "+33123456789",
        "competences": ["Python", "FastAPI", "Machine Learning"],
        "annees_experience": 5,
        "poste_actuel": "Ingénieur logiciel",
    }

    def test_cv_valide(self):
        """Un CV bien formé doit être créé sans erreur."""
        cv = CV(**self.VALID_CV)
        assert cv.nom == "Jean Dupont"
        assert cv.email == "jean.dupont@email.com"
        assert cv.annees_experience == 5
        assert cv.poste_actuel == "Ingénieur logiciel"
        assert len(cv.competences) == 3

    def test_cv_obligatoire_champs_manquants(self):
        """Vérifie que tous les champs requis lèvent une erreur si absents."""
        required_fields = ["nom", "email", "telephone", "competences", "annees_experience", "poste_actuel"]
        for field in required_fields:
            data = self.VALID_CV.copy()
            del data[field]
            with pytest.raises(ValidationError) as excinfo:
                CV(**data)
            assert field in str(excinfo.value)

    def test_cv_email_invalide(self):
        """Un email mal formaté doit lever une erreur."""
        data = self.VALID_CV.copy()
        data["email"] = "pas-un-email"
        with pytest.raises(ValidationError):
            CV(**data)

    def test_cv_competences_doit_etre_une_liste(self):
        """'competences' doit être une liste de chaînes."""
        data = self.VALID_CV.copy()
        data["competences"] = "Python"
        with pytest.raises(ValidationError):
            CV(**data)

    def test_cv_annees_experience_negatif(self):
        """'annees_experience' ne peut pas être négatif (minimum=0)."""
        data = self.VALID_CV.copy()
        data["annees_experience"] = -1
        with pytest.raises(ValidationError):
            CV(**data)

    def test_cv_annees_experience_zero_valide(self):
        """0 an d'expérience est une valeur valide."""
        data = self.VALID_CV.copy()
        data["annees_experience"] = 0
        cv = CV(**data)
        assert cv.annees_experience == 0

    def test_cv_model_dump(self):
        """Vérifie la sérialisation en dictionnaire."""
        cv = CV(**self.VALID_CV)
        d = cv.model_dump()
        assert d["nom"] == "Jean Dupont"
        assert d["email"] == "jean.dupont@email.com"
        assert d["annees_experience"] == 5
