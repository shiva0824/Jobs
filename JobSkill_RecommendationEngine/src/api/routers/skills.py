from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..services.skills_suggester import suggest_skills
from src.api.core.auth import get_current_user

router = APIRouter(prefix="/api/skills", tags=["Skills"])

# Autocomplete skill suggestions.
@router.get("/suggest", response_model=List[str])
def suggest(q: str, limit: int = 10, user: str = Depends(get_current_user)):
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    return suggest_skills(q, limit)