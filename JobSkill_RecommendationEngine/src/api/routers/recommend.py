from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from pydantic import BaseModel
from ..services.recommender import recommend_jobs
from src.api.core.auth import get_current_user


router = APIRouter(prefix="/api/recommend", tags=["Recommendation"])


class ResumeSkillsRequest(BaseModel):
    resume_skills: Dict[str, List[str]]


@router.post("/jobs")
async def recommend_jobs_endpoint(
    request: ResumeSkillsRequest,
    user: str = Depends(get_current_user)
):
    resume_skills = request.resume_skills

    if not resume_skills or (
        not resume_skills.get("technical") and not resume_skills.get("soft")
    ):
        raise HTTPException(status_code=400, detail="Must provide at least one skill")

    try:
        recs = recommend_jobs(resume_skills)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

    return {"recommendations": recs}