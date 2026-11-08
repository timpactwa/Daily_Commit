import os
import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from api import db, repo, skill_levels
from api.deps import client_date, current_user, demo_mode, today_for
from api.errors import invalid_response
from api.routes.answers import ResponseValue, record_answer
from engine import elo, placement

router = APIRouter(prefix="/v1")


class PlacementResponse(BaseModel):
    question_id: str
    response: ResponseValue
    time_ms: int | None = Field(default=None, ge=0)


class PlacementIn(BaseModel):
    responses: list[PlacementResponse] = Field(min_length=1, max_length=20)


def topic_levels(ratings: dict[str, float]) -> list[dict]:
    return [
        {"topic": t, "rating": round(r), "level": skill_levels.describe(r)["level"], "readiness": elo.readiness(r)}
        for t in repo.TOPIC_TRACK
        if (r := ratings.get(t)) is not None
    ]


DEFAULT_DEMO_PLACEMENT_LIMIT = 4


def effective_limit(requested: int | None) -> int | None:
    """Placement size. Outside DEMO_MODE always the full test. In DEMO_MODE an explicit
    ?limit wins; otherwise DEMO_PLACEMENT_LIMIT (default 4; 0 = full test) keeps the
    live demo short without the app having to know it is a demo."""
    if not demo_mode():
        return None
    if requested is not None:
        return requested
    try:
        configured = int(os.environ.get("DEMO_PLACEMENT_LIMIT", DEFAULT_DEMO_PLACEMENT_LIMIT))
    except ValueError:
        configured = DEFAULT_DEMO_PLACEMENT_LIMIT
    return configured if 2 <= configured <= 10 else None


@router.get("/placement")
def get_placement(
    limit: int | None = Query(default=None, ge=2, le=10),
    user: sqlite3.Row = Depends(current_user),
    conn: sqlite3.Connection = Depends(db.get_conn),
):
    flagged = repo.candidates(conn, placement_only=True)
    flagged_topics = {c.topic for c in flagged}
    # Prefer flagged questions; topics with none fall back to any active question.
    pool = flagged + [c for c in repo.candidates(conn) if c.topic not in flagged_topics]
    chosen = placement.choose(pool, repo.TOPIC_TRACK, seed=user["id"], limit=effective_limit(limit))
    rows = {r["id"]: r for r in conn.execute(
        f"SELECT * FROM questions WHERE id IN ({','.join('?' * len(chosen))})", [c.id for c in chosen]
    )} if chosen else {}
    return {"questions": [repo.public_question(rows[c.id], shuffle_seed=user["id"]) for c in chosen]}


@router.post("/placement")
def submit_placement(
    body: PlacementIn,
    user: sqlite3.Row = Depends(current_user),
    base: date = Depends(client_date),
    conn: sqlite3.Connection = Depends(db.get_conn),
):
    ids = [r.question_id for r in body.responses]
    if len(set(ids)) != len(ids):
        raise invalid_response("Each placement question can be answered once")
    day = today_for(user, base)

    results = []
    for r in body.responses:
        qrow = repo.question(conn, r.question_id)
        if qrow is None or not qrow["active"]:
            raise invalid_response(f"Unknown question {r.question_id}")
        q, u = record_answer(conn, user["id"], qrow, r.response, "placement", day, None, r.time_ms)
        ratings = repo.ratings(conn, user["id"])
        conn.executemany(
            "UPDATE user_topics SET rating = ? WHERE user_id = ? AND topic = ?",
            [(v, user["id"], t) for t, v in placement.spillover(ratings, q["topic"], u.student_delta, repo.TOPIC_TRACK).items()],
        )
        results.append({"question_id": q["id"], "correct": u.score == 1.0})

    conn.execute("UPDATE users SET placed = 1 WHERE id = ?", (user["id"],))
    return {"results": results, "topics": topic_levels(repo.ratings(conn, user["id"]))}
