import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import Analysis
from app.services.file_parser import parse_cv
from app.services.analyzer import compute_match_score, generate_feedback
from app.services.notifications import notify_async, manager
from app.services.notifications import notify_async, manager, build_analysis_payload



router = APIRouter(prefix="/analyses", tags=["analyses"])


# ── Schémas ─────────────────────────────────────────────────────────────────

class AnalysisCreate(BaseModel):
    cv_filename: Optional[str] = None
    job_title: Optional[str] = ""
    candidate_name: Optional[str] = ""
    cv_text: Optional[str] = ""


class AnalysisResponse(BaseModel):
    id: str
    candidate_name: str = ""
    job_title: str = ""
    cv_filename: str
    cv_text: str = ""
    score: Optional[float] = None
    status: str = "pending"
    feedback: str = ""
    skills_found: list = []
    skills_missing: list = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Helper ──────────────────────────────────────────────────────────────────

def _format_response(a: Analysis) -> AnalysisResponse:
    """Convertit un modèle SQLAlchemy en schéma de réponse."""
    result_data = {}
    if a.result_json:
        try:
            result_data = json.loads(a.result_json)
        except (json.JSONDecodeError, TypeError):
            result_data = {}

    return AnalysisResponse(
        id=str(a.id),
        candidate_name=result_data.get("candidate_name", ""),
        job_title=a.job_title or result_data.get("job_title", ""),
        cv_filename=a.cv_filename or "",
        cv_text=result_data.get("cv_text", ""),
        score=a.score,
        status=a.status or "pending",
        feedback=result_data.get("feedback", ""),
        skills_found=result_data.get("skills_found", []),
        skills_missing=result_data.get("skills_missing", []),
        created_at=a.created_at,
    )


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.post("", response_model=AnalysisResponse, status_code=201)
def create_analysis(payload: AnalysisCreate, db: Session = Depends(get_db)):
    """Crée une analyse manuellement."""
    analysis_id = str(uuid.uuid4())
    filename = payload.cv_filename or f"cv_{analysis_id[:8]}.pdf"

    result_data = {
        "candidate_name": payload.candidate_name or "",
        "cv_text": payload.cv_text or "",
    }

    analysis = Analysis(
        id=analysis_id,
        cv_filename=filename,
        job_title=payload.job_title or "",
        score=None,
        status="pending",
        result_json=json.dumps(result_data),
        created_at=datetime.now(timezone.utc),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _format_response(analysis)


@router.get("", response_model=dict)
def list_analyses(
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Éléments par page"),
    sort_by: str = Query("created_at", description="Colonne de tri"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Ordre de tri"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Score minimum"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    keyword: Optional[str] = Query(None, description="Recherche textuelle"),
    db: Session = Depends(get_db),
):
    """Liste les analyses avec pagination, tri et filtres."""
    query = db.query(Analysis)

    # ── Filtres ──
    if min_score is not None:
        query = query.filter(Analysis.score >= min_score)
    if status:
        query = query.filter(Analysis.status == status)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                Analysis.cv_filename.ilike(like),
                Analysis.job_title.ilike(like),
                Analysis.result_json.ilike(like),
            )
        )

    # ── Tri sécurisé ──
    allowed_columns = {
        "created_at": Analysis.created_at,
        "score": Analysis.score,
        "status": Analysis.status,
        "job_title": Analysis.job_title,
        "cv_filename": Analysis.cv_filename,
    }
    column = allowed_columns.get(sort_by, Analysis.created_at)
    order_func = column.desc if order == "desc" else column.asc
    query = query.order_by(order_func())

    # ── Pagination ──
    total = query.count()
    analyses = query.offset((page - 1) * size).limit(size).all()

    return {
        "items": [_format_response(a) for a in analyses],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0,
    }
    

@router.get("/ranking", response_model=dict)
def ranking_analyses(
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Score minimum"),
    limit: int = Query(50, ge=1, le=200, description="Nombre max de résultats"),
    db: Session = Depends(get_db),
):
    """Classement des candidats par score décroissant."""
    query = db.query(Analysis).filter(Analysis.score.isnot(None))

    if status:
        query = query.filter(Analysis.status == status)
    if min_score is not None:
        query = query.filter(Analysis.score >= min_score)

    analyses = query.order_by(Analysis.score.desc()).limit(limit).all()

    ranking = []
    for rank, a in enumerate(analyses, start=1):
        result = json.loads(a.result_json) if a.result_json else {}
        ranking.append({
            "rank": rank,
            "id": a.id,
            "cv_filename": a.cv_filename,
            "candidate_name": result.get("candidate_name", ""),
            "job_title": a.job_title,
            "score": a.score,
            "status": a.status,
            "feedback": result.get("feedback", ""),
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return {
        "total": len(ranking),
        "ranking": ranking,
    }



@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Récupère une analyse par son ID."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    return _format_response(analysis)


@router.delete("/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Supprime une analyse."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    db.delete(analysis)
    db.commit()


@router.post("/upload", response_model=AnalysisResponse, status_code=201)
async def upload_cv(
    file: UploadFile = File(...),
    candidate_name: str = Form(""),
    job_title: str = Form(""),
    db: Session = Depends(get_db),
):
    """Upload un CV et crée une analyse."""
    analysis_id = str(uuid.uuid4())
    filename = file.filename or f"cv_{analysis_id[:8]}.pdf"

    file_bytes = file.file.read()
    filepath, cv_text = parse_cv(file_bytes, file.filename or "document.pdf")


    result_data = {
        "candidate_name": candidate_name,
        "cv_text": cv_text,
    }

    analysis = Analysis(
        id=analysis_id,
        cv_filename=filename,
        job_title=job_title,
        score=0.0,
        status="pending",
        result_json=json.dumps(result_data),
        created_at=datetime.now(timezone.utc),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _format_response(analysis)


@router.post("/{analysis_id}/analyze", response_model=AnalysisResponse)
def analyze_cv(analysis_id: str, db: Session = Depends(get_db)):
    """Lance l'analyse de correspondance CV / poste."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")

    result_data = {}
    if analysis.result_json:
        try:
            result_data = json.loads(analysis.result_json)
        except (json.JSONDecodeError, TypeError):
            result_data = {}

    cv_text = result_data.get("cv_text", "")
    job_title = analysis.job_title or ""

    if not cv_text:
        raise HTTPException(status_code=400, detail="Aucun texte de CV disponible")

    # Utilisation des vraies fonctions du service
    match_result = compute_match_score(cv_text, job_title)
    feedback = generate_feedback(match_result)

    result_data["score"] = match_result["score"]
    result_data["feedback"] = feedback
    result_data["skills_found"] = match_result["matched_skills"]
    result_data["skills_missing"] = match_result["missing_skills"]

    analysis.score = match_result["score"]
    analysis.status = "completed"
    analysis.result_json = json.dumps(result_data)
    db.commit()
    db.refresh(analysis)
        # ── Notifications (fire & forget) ──
    notify_async(
        db_analysis,
        webhook_url="",           # ← mets ton URL Slack/Discord ici ou vide
        smtp_config=None,         # ← configure plus bas
        email_to="",
    )

    # ── WebSocket broadcast ──
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(manager.broadcast(build_analysis_payload(db_analysis)))
    except Exception:
        pass

    return _format_response(analysis)


@router.get("/export/csv")
def export_csv(
    min_score: Optional[float] = Query(None, ge=0, le=100),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Exporte les analyses au format CSV."""
    query = db.query(Analysis)

    if min_score is not None:
        query = query.filter(Analysis.score >= min_score)
    if status:
        query = query.filter(Analysis.status == status)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                Analysis.cv_filename.ilike(like),
                Analysis.job_title.ilike(like),
                Analysis.result_json.ilike(like),
            )
        )

    analyses = query.order_by(Analysis.created_at.desc()).all()

    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Candidat", "Poste", "Fichier", "Score", "Statut", "Date"])

    for a in analyses:
        result_data = {}
        if a.result_json:
            try:
                result_data = json.loads(a.result_json)
            except (json.JSONDecodeError, TypeError):
                pass
        writer.writerow([
            a.id,
            result_data.get("candidate_name", ""),
            a.job_title or "",
            a.cv_filename or "",
            a.score or "",
            a.status or "",
            a.created_at.isoformat() if a.created_at else "",
        ])

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analyses.csv"},
    )
