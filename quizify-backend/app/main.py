from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401  (ensures models are registered before create_all)
from app.routers import auth, subjects, uploads, quizzes, flashcards, analytics, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Quizify API",
    description="AI-powered reviewer backend for students.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(subjects.router)
app.include_router(uploads.router)
app.include_router(quizzes.router)
app.include_router(flashcards.router)
app.include_router(analytics.router)
app.include_router(admin.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


# Serve the frontend (index.html + logo.png) at "/". Mounted AFTER all API
# routers so API routes and /health always take precedence; html=True makes
# "/" resolve to index.html.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
