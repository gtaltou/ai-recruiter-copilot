import csv
import json
import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/export", tags=["Export"])

@router.get("/csv")
async def export_csv():
    """Exporte les dernières analyses au format CSV."""
    # Exemple statique — à connecter à la base réelle
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["candidate", "job_title", "match_score", "status"])
    writer.writerow(["John Doe", "Senior ML Engineer", 93.5, "Shortlisted"])
    writer.writerow(["Jane Smith", "Senior ML Engineer", 78.2, "Reviewed"])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analyses.csv"}
    )

@router.get("/json")
async def export_json():
    """Exporte les dernières analyses au format JSON."""
    data = [
        {"candidate": "John Doe", "job_title": "Senior ML Engineer", "match_score": 93.5, "status": "Shortlisted"},
        {"candidate": "Jane Smith", "job_title": "Senior ML Engineer", "match_score": 78.2, "status": "Reviewed"}
    ]
    return JSONResponse(content=data)