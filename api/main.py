"""Daily Commit API. Run from repo root: uvicorn api.main:app --reload --port 8000"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import content_loader, db, errors
from api.routes import answers, lessons, placement, progress, users

ROOT = Path(__file__).resolve().parent.parent
APP_DIST = ROOT / "app" / "dist"
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Boot: schema, then reload /content (keeps learned ratings). Demo reset is added in P3.
    db.init()
    with db.transaction() as conn:
        app.state.question_count = content_loader.load(conn)
    yield


app = FastAPI(title="Daily Commit API", version="1", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
errors.install(app)
app.state.question_count = 0

for r in (users.router, placement.router, lessons.router, answers.router, progress.router):
    app.include_router(r)


@app.get("/health")
def health():
    return {"ok": True, "questions": app.state.question_count}


# Production: serve the built app at "/". Must be mounted after all API routes.
if APP_DIST.is_dir():
    app.mount("/", StaticFiles(directory=APP_DIST, html=True), name="app")
