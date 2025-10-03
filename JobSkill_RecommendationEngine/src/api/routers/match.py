from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from ..services.matcher import match_resume_to_jd
from src.api.core.auth import get_current_user

router = APIRouter(prefix="/api/match", tags=["Match"])

class ResumeSkills(BaseModel):
    technical: List[str]
    soft: List[str]

class MatchRequest(BaseModel):
    job_description: str
    resume_skills: ResumeSkills

@router.post("/")
async def match_endpoint(payload: MatchRequest, user: str = Depends(get_current_user)):
    if not payload.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    result = match_resume_to_jd(
        resume_skills=payload.resume_skills.dict(),
        job_description=payload.job_description,
    )
    return result