import os
from pathlib import Path
from PyPDF2 import PdfReader
from docx import Document


UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def extract_text_from_pdf(filepath: str) -> str:
    reader = PdfReader(filepath)
    return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())


def extract_text_from_docx(filepath: str) -> str:
    doc = Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs)


def save_upload(file_bytes: bytes, filename: str) -> str:
    """Sauvegarde le fichier et retourne le chemin."""
    filepath = UPLOAD_DIR / filename
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    return str(filepath)


def parse_cv(file_bytes: bytes, filename: str) -> tuple[str, str]:
    """Sauvegarde et extrait le texte d'un CV. Retourne (filepath, text)."""
    ext = Path(filename).suffix.lower()
    filepath = save_upload(file_bytes, filename)

    if ext == ".pdf":
        text = extract_text_from_pdf(filepath)
    elif ext == ".docx":
        text = extract_text_from_docx(filepath)
    else:
        raise ValueError(f"Format non supporté : {ext}. Utilisez .pdf ou .docx")

    return filepath, text
