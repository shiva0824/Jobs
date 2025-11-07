from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import resume, match, recommend, skills  # Phase 2
from src.api.routers import auth  # Phase 1 (re-use login)

app = FastAPI(
    title="Job Skill Recommendation Engine API",
    version="0.1.0",
    description="Resume parsing, skill suggestions, matching, and job recommendations",
)

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://127.0.0.1:5500", "http://localhost:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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