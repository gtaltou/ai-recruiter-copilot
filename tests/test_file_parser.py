import pytest
import io
from pathlib import Path
from unittest.mock import patch
from docx import Document
from app.services.file_parser import parse_cv, save_upload


class TestFileParser:

    def test_save_upload(self, tmp_path):
        """save_upload écrit les bytes sur le disque et retourne le chemin."""
        content = b"Hello, World!"
        filename = "test.txt"

        with patch("app.services.file_parser.UPLOAD_DIR", tmp_path):
            result = save_upload(content, filename)

        expected_path = tmp_path / filename
        assert result == str(expected_path)
        assert expected_path.read_bytes() == content

    def test_parse_cv_docx_success(self, tmp_path):
        """parse_cv extrait le texte d'un fichier .docx valide."""
        doc = Document()
        doc.add_paragraph("Compétences: Python, FastAPI")
        doc.add_paragraph("Expérience: 5 ans")
        buf = io.BytesIO()
        doc.save(buf)
        content = buf.getvalue()

        with patch("app.services.file_parser.UPLOAD_DIR", tmp_path):
            filepath, text = parse_cv(content, "cv.docx")

        assert Path(filepath).exists()
        assert "Python" in text
        assert "FastAPI" in text

    def test_parse_cv_unsupported_format(self, tmp_path):
        """parse_cv lève ValueError pour un format non supporté."""
        with patch("app.services.file_parser.UPLOAD_DIR", tmp_path):
            with pytest.raises(ValueError, match="Format non supporté"):
                parse_cv(b"test", "cv.txt")

    def test_parse_cv_invalid_pdf(self, tmp_path):
        """parse_cv lève ValueError pour un PDF corrompu."""
        with patch("app.services.file_parser.UPLOAD_DIR", tmp_path):
            with pytest.raises(ValueError, match="corrompu|invalide"):
                parse_cv(b"pas un pdf valide", "cv.pdf")
