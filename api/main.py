"""Daily Commit API. Run from repo root: uvicorn api.main:app --reload --port 8000"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import errors

ROOT = Path(__file__).resolve().parent.parent
APP_DIST = ROOT / "app" / "dist"

app = FastAPI(title="Daily Commit API", version="1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
errors.install(app)
app.state.question_count = 0  # set by the content loader (T2)


@app.get("/health")
def health():
    return {"ok": True, "questions": app.state.question_count}


# Production: serve the built app at "/". Must be mounted after all API routes.
if APP_DIST.is_dir():
    app.mount("/", StaticFiles(directory=APP_DIST, html=True), name="app")
