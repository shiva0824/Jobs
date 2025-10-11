import psycopg2
from psycopg2.extras import DictCursor
from typing import Dict, List
from JobSkill_RecommendationEngine.src.core.config import settings


# -------------------------------
# DB connection settings
# -------------------------------
DB_CONFIG = {
    "dbname": settings.DB_NAME,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "host": settings.DB_HOST,
    "port": settings.DB_PORT
}

# -------------------------------
# Core recommender
# -------------------------------
def recommend_jobs(skills: Dict[str, List[str]], top_n: int = 10) -> List[Dict]:
    technical = {s.lower().strip() for s in skills.get("technical", [])}
    soft = {s.lower().strip() for s in skills.get("soft", [])}

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=DictCursor)

    # Get all roles and their skills
    cur.execute("""
        SELECT r.id, r.title, r.level,
               ARRAY_AGG(s.name) FILTER (WHERE s.type='technical') AS technical,
               ARRAY_AGG(s.name) FILTER (WHERE s.type='soft') AS soft
        FROM roles r
        JOIN role_skills rs ON r.id = rs.role_id
        JOIN skills s ON s.id = rs.skill_id
        GROUP BY r.id, r.title, r.level
    """)
    rows = cur.fetchall()

    recommendations = []
    for row in rows:
        job_tech = {s.lower() for s in (row["technical"] or [])}
        job_soft = {s.lower() for s in (row["soft"] or [])}

        matched_tech = sorted(list(technical & job_tech))
        missing_tech = sorted(list(job_tech - technical))
        extra_tech = sorted(list(technical - job_tech))

        matched_soft = sorted(list(soft & job_soft))
        missing_soft = sorted(list(job_soft - soft))
        extra_soft = sorted(list(soft - job_soft))

        # Simple weighted score
        score = 0.0
        if job_tech:
            score += 0.7 * (len(matched_tech) / len(job_tech)) * 100
        if job_soft:
            score += 0.3 * (len(matched_soft) / len(job_soft)) * 100

        recommendations.append({
            "title": row["title"],
            "level": row["level"],
            "score": round(score, 2),
            "breakdown": {
                "technical": {
                    "matched": matched_tech,
                    "missing": missing_tech,
                    "extra": extra_tech
                },
                "soft": {
                    "matched": matched_soft,
                    "missing": missing_soft,
                    "extra": extra_soft
                }
            }
        })

    cur.close()
    conn.close()

    # sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    return recommendations[:top_n]