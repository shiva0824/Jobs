from typing import Dict, List, Set
from src.api.services.inference import extract_skills # Phase 1 JD extractor
from ..services.resume_parser import sanitize_skill

def _jaccard(set1: Set[str], set2: Set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)

def _compare(resume_set: Set[str], jd_set: Set[str]) -> Dict[str, List[str]]:
    """Return matched, missing, and extra skills."""
    matched = resume_set & jd_set
    missing = jd_set - resume_set
    extra = resume_set - jd_set
    return {
        "matched": sorted(matched),
        "missing": sorted(missing),
        "extra": sorted(extra),
    }

def match_resume_to_jd(resume_skills: Dict[str, List[str]], job_description: str) -> Dict:
    """
    Compare resume skills with JD skills (extracted using Phase 1 model).
    Weighted Jaccard: 0.7 technical + 0.3 soft.
    """
    # normalize + dedup resume skills
    tech_resume = {sanitize_skill(s).lower() for s in resume_skills.get("technical", []) if s}
    soft_resume = {sanitize_skill(s).lower() for s in resume_skills.get("soft", []) if s}

    # extract JD skills using Phase 1 pipeline
    jd_result = extract_skills(job_description)
    tech_jd = {s.lower() for s in jd_result.get("technical_skills", [])}
    soft_jd = {s.lower() for s in jd_result.get("soft_skills", [])}

    # comparisons
    tech_compare = _compare(tech_resume, tech_jd)
    soft_compare = _compare(soft_resume, soft_jd)

    # scores
    tech_score = _jaccard(tech_resume, tech_jd)
    soft_score = _jaccard(soft_resume, soft_jd)
    match_score = round(100 * (0.7 * tech_score + 0.3 * soft_score), 2)

    return {
        "match_score": match_score,
        "technical": tech_compare,
        "soft": soft_compare,
    }