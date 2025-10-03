from fastapi import FastAPI
from .routers import resume, match, recommend, skills  # Phase 2
from src.api.routers import auth  # Phase 1 (re-use login)

app = FastAPI(
    title="Job Skill Recommendation Engine API (Phase 2)",
    version="0.1.0",
    description="Phase 2: Resume parsing, skill suggestions, matching, and job recommendations",
)

# Include routers
app.include_router(auth.router)     # /auth/login from Phase 1
app.include_router(resume.router)   # /api/resume/parse (Phase 2)
app.include_router(match.router)     # /api/match (Phase 2)
app.include_router(recommend.router)  # /api/recommend (Phase 2)
app.include_router(skills.router)   # /api/skills (Phase 2)

@app.get("/health")
def health_check():
    return {"status": "ok", "phase": 2}