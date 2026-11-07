"""Daily Commit API. Run from repo root: uvicorn api.main:app --reload --port 8000"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from api import content_loader, db, errors, seed_demo, seed_ranked
from api.deps import demo_mode
from api.routes import answers, auth, demo, learn, lessons, placement, progress, ranked, users

ROOT = Path(__file__).resolve().parent.parent
APP_DIST = ROOT / "app" / "dist"
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Boot: schema, reload /content (keeps learned ratings), reset the demo user.
    db.init()
    with db.transaction() as conn:
        app.state.question_count = content_loader.load(conn)
        if demo_mode():
            seed_ranked.seed(conn)
        seed_demo.reset(conn, datetime.now(timezone.utc).date().isoformat())
    yield


app = FastAPI(title="Daily Commit API", version="1", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
errors.install(app)
app.state.question_count = 0

for r in (users.router, auth.router, placement.router, lessons.router, answers.router, progress.router,
          learn.router, ranked.router, demo.router):
    app.include_router(r)


@app.get("/health")
def health():
    return {"ok": True, "questions": app.state.question_count}


class SpaFiles(StaticFiles):
    """Static app files; unknown non-API paths get index.html so deep links and refreshes
    (e.g. /ranked/beginner/play) load the app instead of a 404."""

    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as e:
            p = path.replace("\\", "/")  # Starlette uses os.sep on Windows
            if e.status_code != 404 or p.startswith(("v1/", "health")) or "." in p.rsplit("/", 1)[-1]:
                raise
            return await super().get_response("index.html", scope)


# Production: serve the built app at "/". Must be mounted after all API routes.
if APP_DIST.is_dir():
    app.mount("/", SpaFiles(directory=APP_DIST, html=True), name="app")
