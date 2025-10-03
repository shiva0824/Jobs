from pathlib import Path
from typing import Dict, List, Union
import json
import pdfplumber
import docx
import re
import os

# -------------------------------
# Sanitization helpers
# -------------------------------
def sanitize_skill(skill: str) -> str:
    """Normalize skill string: strip, collapse spaces, remove artifacts/symbols."""
    if not skill:
        return ""
    clean = re.sub(r"<[^>]+>", "", skill)
    clean = re.sub(r"\(cid:\d+\)", "", clean)   # remove PDF artifacts
    clean = clean.strip(" -–—•·")
    clean = re.sub(r"\s+", " ", clean)
    return clean

def _explode_candidates(raw: str) -> List[str]:
    """Split composite strings on delimiters into candidate skills."""
    if not raw:
        return []
    parts = re.split(r"[,\u2022•;/\|\t:]", raw)
    return [sanitize_skill(p) for p in parts if sanitize_skill(p)]

def _extract_name_heuristic(text: str) -> str:
    """Pick first header-like line that isn't contact/social."""
    for line in text.splitlines():
        clean = re.sub(r"\(cid:\d+\)", "", line or "").strip()
        if not clean:
            continue
        lc = clean.lower()
        if "@" in lc or "linkedin" in lc or "github" in lc or "phone" in lc:
            continue
        tokens = clean.split()
        if 1 < len(tokens) <= 5 and sum(t.isalpha() for t in tokens) >= len(tokens) - 1:
            return clean
        return clean
    return ""

def _extract_experience_years(text: str) -> str:
    """Regex-scan text for 'X years/yrs' patterns and pick max."""
    t = re.sub(r"\s+", " ", text.lower())
    pattern = r'(?:(?:over|more than|approximately|around)\s+)?(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)'
    years: List[float] = []
    for m in re.finditer(pattern, t):
        try:
            years.append(float(m.group(1)))
        except Exception:
            pass
    if years:
        y = max(years)
        return f"{int(y)} years" if y.is_integer() else f"{y} years"
    return "0 (Fresher)"

# -------------------------------
# Load soft-skill dictionary
# -------------------------------
SKILL_PHRASES_PATH = Path(__file__).resolve().parents[4] / "data" / "skill_phrases.json"
with open(SKILL_PHRASES_PATH, "r", encoding="utf-8") as f:
    skill_dict = json.load(f)
soft_skill_lookup = {s.lower().strip() for s in skill_dict.get("SOFT_SKILL_PHRASES", [])}

# -------------------------------
# File text extraction
# -------------------------------
def extract_text_from_pdf(file_path: Union[str, Path]) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
            text += "\n"
    return text.strip()

def extract_text_from_docx(file_path: Union[str, Path]) -> str:
    doc = docx.Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text).strip()

# -------------------------------
# Section-based fallback
# -------------------------------
SKILL_HEADERS = [
    "skills", "key skills", "core skills", "technical skills", "professional skills",
    "relevant skills", "specialized skills", "hard skills", "soft skills",
    "tools & technologies", "technologies", "competencies", "core competencies",
    "technical competencies", "areas of expertise", "expertise", "key strengths",
    "strengths", "proficiencies", "technical proficiencies", "knowledge areas",
    "professional competencies", "capabilities"
]

STOP_HEADERS = [
    "education", "experience", "work experience", "projects", "academic projects",
    "professional experience", "achievements", "extracurricular", "certifications",
    "publications", "research", "activities"
]

def _extract_skills_section(text: str, max_chars: int = 600, max_lines: int = 10) -> List[str]:
    lowered = text.lower()
    header_pattern = r"|".join([re.escape(h) for h in SKILL_HEADERS])
    match = re.search(rf"({header_pattern})[:\n](.*)", lowered, flags=re.DOTALL)
    if not match:
        return []

    block = match.group(2)

    # stop at next known section header
    for stop in STOP_HEADERS:
        idx = block.find(stop)
        if idx != -1:
            block = block[:idx]
            break

    # fallback cutoff
    block_lines = block.splitlines()
    if len(block_lines) > max_lines:
        block = "\n".join(block_lines[:max_lines])
    if len(block) > max_chars:
        block = block[:max_chars]

    candidates = _explode_candidates(block)
    return candidates

# -------------------------------
# Main parser
# -------------------------------
def parse_resume(file_path: Union[str, Path]) -> Dict:
    # 1) Extract text
    ext = str(file_path).lower()
    if ext.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif ext.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format (only PDF/DOCX)")

    if not text:
        return {
            "name": "",
            "skills": {"technical": [], "soft": []},
            "experience": "0 (Fresher)",
            "message": "Could not read resume text. File may be an image-based PDF. Please enter skills manually."
        }

    # 2) Section scan
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    section_candidates = _extract_skills_section(text)
    for cand in section_candidates:
        if cand.lower() in soft_skill_lookup:
            soft_skills.append(cand)
        else:
            technical_skills.append(cand)

    # Dedup & sort
    technical_skills = sorted(set(technical_skills))
    soft_skills = sorted(set(soft_skills))

    # 3) Name & experience
    name = _extract_name_heuristic(text)
    experience = _extract_experience_years(text)

    # 4) Final check: if still no skills → include message
    result: Dict = {
        "name": name,
        "skills": {"technical": technical_skills, "soft": soft_skills},
        "experience": experience,
    }
    if not technical_skills and not soft_skills:
        result["message"] = (
            "Could not auto-extract skills. Your PDF may be an image "
            "or missing a 'Technical Skills' section. Please paste your skills manually."
        )
    return result