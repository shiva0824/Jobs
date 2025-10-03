from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from pathlib import Path
import shutil, tempfile

from ..services.resume_parser import parse_resume
from src.api.core.auth import get_current_user

router = APIRouter(prefix="/api/resume", tags=["Resume"])

@router.post("/parse")
async def parse_resume_endpoint(
    resume_file: UploadFile = File(...),
    user: str = Depends(get_current_user),
):

    fname = (resume_file.filename or "").lower()
    if not (fname.endswith(".pdf") or fname.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Unsupported file format (only PDF/DOCX allowed)")

    suffix = Path(fname).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(resume_file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        result = parse_resume(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    return result