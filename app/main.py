from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1.api import v1_router
from app.core.config import settings
from app.core.middleware import MetricsMiddleware, LoggingMiddleware, JWTAuthMiddleware
from app.core.logging import setup_logging
from app.db import engine, Base
from app.web.router import router as web_router
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from app.db.models import Analysis
from app.db import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import json
from fastapi import WebSocket, WebSocketDisconnect
from app.services.notifications import manager



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup : logging + création des tables."""
    setup_logging(log_level=settings.LOG_LEVEL, log_json=settings.LOG_JSON)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(JWTAuthMiddleware)
templates = Jinja2Templates(directory="app/templates")

@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard(request: Request, db: Session = Depends(get_db)):
    from app.api.v1.endpoints.analyses import get_db as _get_db
    # On récupère le classement directement
    analyses = db.query(Analysis).filter(Analysis.score.isnot(None)).order_by(Analysis.score.desc()).all()

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
        })

    total = len(ranking)
    completed = sum(1 for r in ranking if r["status"] == "completed")
    pending = sum(1 for r in ranking if r["status"] == "pending")
    avg_score = round(sum(r["score"] for r in ranking) / total, 1) if total else 0

    import json as _json
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "ranking": ranking,
        "ranking_json": _json.dumps(ranking, ensure_ascii=False),
        "stats": {
            "total": total,
            "completed": completed,
            "pending": pending,
            "avg_score": avg_score,
        }
    })

app.include_router(v1_router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(web_router)

app.include_router(web_router)


# ── WebSocket endpoint ───────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)



