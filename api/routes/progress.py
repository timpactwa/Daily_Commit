import sqlite3
from datetime import date

from fastapi import APIRouter, Depends

from api import db, repo
from api.deps import client_date, current_user, today_for
from api.routes.users import streak_payload
from engine import elo

router = APIRouter(prefix="/v1")
HISTORY_LEN = 10


@router.get("/progress")
def progress(
    user: sqlite3.Row = Depends(current_user),
    base: date = Depends(client_date),
    conn: sqlite3.Connection = Depends(db.get_conn),
):
    rows = {r["topic"]: r for r in conn.execute("SELECT * FROM user_topics WHERE user_id = ?", (user["id"],))}
    history: dict[str, list[float]] = {}
    for a in conn.execute(
        "SELECT topic, r_after FROM attempts WHERE user_id = ? ORDER BY id", (user["id"],)
    ):
        history.setdefault(a["topic"], []).append(a["r_after"])

    topics = []
    for topic, track in repo.TOPIC_TRACK.items():
        r = rows.get(topic)
        if r is None:
            continue
        points = history.get(topic, [])[-HISTORY_LEN:]
        topics.append({
            "topic": topic,
            "track": track,
            "rating": round(r["rating"]),
            "level": elo.level(r["rating"]),
            "readiness": elo.readiness(r["rating"]),
            "answered": r["answers"],
            "accuracy": round(r["correct"] / r["answers"], 2) if r["answers"] else 0.0,
            "history": [round(p) for p in points] or [round(r["rating"])],
        })
    overall = round(sum(t["readiness"] for t in topics) / len(topics)) if topics else 0
    return {
        "streak": streak_payload(user, today_for(user, base)),
        "overall_readiness": overall,
        "topics": topics,
    }
