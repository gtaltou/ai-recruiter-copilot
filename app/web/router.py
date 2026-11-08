"""Routeur web — pages HTML."""
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.security import create_access_token, verify_token, security_settings
from app.web.dependencies import require_auth
from sqlalchemy import func


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, token: str = Form(...)):
    """Valide un token API et pose un cookie JWT."""
    payload = verify_token(token)
    if payload is None:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Token invalide"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Crée un nouveau token avec le même sub et le met dans un cookie
    access_token = create_access_token(data={"sub": payload.get("sub", "web_user")})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=3600,       # 1 heure
        samesite="lax",
    )
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, _=Depends(require_auth)):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response


@router.get("/dev-token")
async def dev_token():
    """Génère un token de développement pour tester le login."""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": "admin@test.com"})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/api/stats")
async def get_stats(request: Request, _=Depends(require_auth)):
    """Renvoie les KPIs du dashboard au format HTML (pour HTMX)."""
    from app.db import SessionLocal
    from app.db.models import Analysis
    from sqlalchemy import func

    db = SessionLocal()
    try:
        total = db.query(Analysis).count()
        avg_score = db.query(func.avg(Analysis.score)).scalar()
        avg_score = round(avg_score, 1) if avg_score else 0
        last = db.query(Analysis).order_by(Analysis.created_at.desc()).first()
        last_date = last.created_at.strftime("%d/%m/%Y %H:%M") if last else "—"

        return templates.TemplateResponse(
            "partials/stats.html",
            {
                "request": request,
                "total_analyses": total,
                "avg_score": avg_score,
                "last_analysis": last_date,
            }
        )
    finally:
        db.close()


