from pathlib import Path
import json
from typing import List

SKILL_PHRASES_PATH = Path(__file__).resolve().parents[4] / "data" / "skill_phrases.json"

with open(SKILL_PHRASES_PATH, "r", encoding="utf-8") as f:
    skill_dict = json.load(f)

ALL_SKILLS = set()
for key, phrases in skill_dict.items():
    for p in phrases:
        if p and isinstance(p, str):
            ALL_SKILLS.add(p.strip())

ALL_SKILLS = sorted(ALL_SKILLS, key=str.lower)


def suggest_skills(query: str, limit: int = 10) -> List[str]:
    if not query:
        return []
    q = query.lower()

    #1. Prefix matches
    prefix_matches = [s for s in ALL_SKILLS if s.lower().startswith(q)]

    #2. Substring matches (excluding those already in prefix_matches)
    substring_matches = [s for s in ALL_SKILLS if q in s.lower() and s not in prefix_matches]

    results = prefix_matches + substring_matches
    return results[:limit]