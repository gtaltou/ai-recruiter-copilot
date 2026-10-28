from fastapi import APIRouter, HTTPException
from app.schemas.cv import CV
from app.schemas.job_description import JobDescription

router = APIRouter(tags=["Analyze"])


@router.post("/analyze")
async def analyze_cv(cv: CV, job_description: JobDescription):
	return {
		"status": "ok",
		"candidate": cv.nom,
		"poste": job_description.titre,
		"score_global": 85.0,
		"recommandation": "À convoquer",
	}
