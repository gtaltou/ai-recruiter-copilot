import re
from typing import Dict, List, Tuple

# --- Dictionnaire de compétences par catégorie ---

SKILL_DB: Dict[str, List[str]] = {
    "python": ["python", "django", "flask", "fastapi", "pandas", "numpy", "pytest", "celery"],
    "javascript": ["javascript", "typescript", "react", "vue", "angular", "node", "nextjs"],
    "backend": ["api", "rest", "graphql", "microservices", "docker", "kubernetes", "postgresql", "mongodb", "redis", "sql", "nosql"],
    "frontend": ["html", "css", "sass", "tailwind", "bootstrap", "responsive"],
    "devops": ["ci/cd", "github actions", "gitlab ci", "jenkins", "terraform", "aws", "gcp", "azure", "linux"],
    "soft_skills": ["leadership", "teamwork", "communication", "agile", "scrum", "problem solving", "autonomy"],
    "data": ["machine learning", "deep learning", "nlp", "data analysis", "sql", "tableau", "power bi"],
    "mobile": ["swift", "kotlin", "flutter", "react native", "android", "ios"],
}

# Synonymes courants pour normaliser
SYNONYM_MAP = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "gcp": "google cloud",
    "aws": "amazon web services",
}


def normalize_text(text: str) -> str:
    """Normalise le texte : lowercase, supprime la ponctuation excessive."""
    text = text.lower()
    text = re.sub(r"[^\w\s/+#]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords(text: str) -> Dict[str, List[str]]:
    """Extrait les compétences trouvées dans un texte, par catégorie."""
    normalized = normalize_text(text)
    found: Dict[str, List[str]] = {}

    for category, skills in SKILL_DB.items():
        matches = []
        for skill in skills:
            # Vérifie si le skill (ou un synonyme) est présent
            if skill in normalized:
                matches.append(skill)
            # Vérifie les synonymes
            for synonym, canonical in SYNONYM_MAP.items():
                if canonical == skill and synonym in normalized:
                    matches.append(skill)
        if matches:
            found[category] = list(set(matches))

    return found


def compute_match_score(cv_text: str, job_text: str) -> dict:
    """
    Calcule le score de correspondance entre un CV et une description de poste.

    Retourne un dict avec :
      - score: float 0-100
      - matched_skills: compétences trouvées dans les deux
      - missing_skills: compétences demandées mais absentes du CV
      - extra_skills: compétences du CV non demandées
      - breakdown: score par catégorie
    """
    cv_keywords = extract_keywords(cv_text)
    job_keywords = extract_keywords(job_text)

    all_job_skills = set()
    for skills in job_keywords.values():
        all_job_skills.update(skills)

    all_cv_skills = set()
    for skills in cv_keywords.values():
        all_cv_skills.update(skills)

    matched = all_job_skills & all_cv_skills
    missing = all_job_skills - all_cv_skills
    extra = all_cv_skills - all_job_skills

    # Score par catégorie
    breakdown = {}
    total_weight = 0
    weighted_score = 0.0

    for category, job_skills in job_keywords.items():
        cv_skills_in_cat = cv_keywords.get(category, [])
        job_set = set(job_skills)
        cv_set = set(cv_skills_in_cat)

        if not job_set:
            continue

        cat_matched = job_set & cv_set
        cat_score = len(cat_matched) / len(job_set) * 100

        # Pondération : backend/devops/data comptent plus
        weight = 1.5 if category in ("backend", "devops", "data") else 1.0

        breakdown[category] = {
            "score": round(cat_score, 1),
            "matched": list(cat_matched),
            "missing": list(job_set - cv_set),
            "weight": weight,
        }
        total_weight += weight
        weighted_score += cat_score * weight

    # Score global
    if total_weight > 0:
        global_score = round(weighted_score / total_weight, 1)
    else:
        # Fallback : matching lexical général
        if all_job_skills:
            global_score = round(len(matched) / len(all_job_skills) * 100, 1)
        else:
            global_score = 50.0  # neutre si aucune compétence détectée

    # Bonus : années d'expérience (pattern simple)
    exp_match = re.findall(r"(\d+)\s*(?:ans?|years?|années?|yr)s?", normalize_text(cv_text))
    job_exp_match = re.findall(r"(\d+)\s*(?:ans?|years?|années?|yr)s?", normalize_text(job_text))

    experience_bonus = 0
    if exp_match and job_exp_match:
        cv_exp = max(int(e) for e in exp_match)
        req_exp = max(int(e) for e in job_exp_match)
        if cv_exp >= req_exp:
            experience_bonus = 5
        elif cv_exp >= req_exp * 0.7:
            experience_bonus = 2

    final_score = min(100, round(global_score + experience_bonus, 1))

    return {
        "score": final_score,
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "extra_skills": sorted(extra),
        "breakdown": breakdown,
        "experience_bonus": experience_bonus,
        "total_required": len(all_job_skills),
        "total_matched": len(matched),
    }


def generate_feedback(result: dict) -> str:
    """Génère un résumé en français à partir du résultat d'analyse."""
    score = result["score"]
    matched = result["matched_skills"]
    missing = result["missing_skills"]
    extra = result["extra_skills"]

    if score >= 80:
        level = "✅ Très bon match"
    elif score >= 60:
        level = "⚠️ Match moyen"
    else:
        level = "❌ Match insuffisant"

    lines = [f"**{level}** — Score : {score}/100\n"]

    if matched:
        lines.append(f"✅ Compétences correspondantes ({len(matched)}) : {', '.join(matched[:10])}")
    if missing:
        lines.append(f"❌ Compétences manquantes ({len(missing)}) : {', '.join(missing[:10])}")
    if extra:
        lines.append(f"💡 Compétences supplémentaires ({len(extra)}) : {', '.join(extra[:5])}")

    if result.get("breakdown"):
        lines.append("\n📊 **Détail par catégorie :**")
        for cat, data in sorted(result["breakdown"].items()):
            icon = "✅" if data["score"] >= 60 else "⚠️" if data["score"] >= 30 else "❌"
            lines.append(f"  {icon} {cat} : {data['score']}/100")

    return "\n".join(lines)
