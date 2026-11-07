import sqlite3
from datetime import date, timedelta

from fastapi import APIRouter, Depends

from api import db, history, repo
from api.deps import client_date, current_user, demo_mode, today_for
from api.errors import ApiError
from engine.selection import LESSON_SIZE, Pick, build_lesson

DEMO_LESSON_SIZE = 3

router = APIRouter(prefix="/v1")


def lesson_id_for(user_id: str, day: str) -> str:
    return f"l_{day}_{user_id}"


def lesson_payload(conn: sqlite3.Connection, lesson: sqlite3.Row) -> dict:
    items = conn.execute(
        """SELECT li.position, li.kind, q.*, a.correct AS a_correct, a.id AS a_id
           FROM lesson_items li
           JOIN questions q ON q.id = li.question_id
           LEFT JOIN attempts a ON a.lesson_id = li.lesson_id AND a.question_id = li.question_id
           WHERE li.lesson_id = ? ORDER BY li.position""",
        (lesson["id"],),
    ).fetchall()
    focus: list[str] = []
    for r in items:
        if r["kind"] == "focus" and r["topic"] not in focus:
            focus.append(r["topic"])
    return {
        "lesson_id": lesson["id"],
        "date": lesson["date"],
        "status": lesson["status"],
        "focus_topics": focus,
        "items": [
            {
                "position": r["position"],
                "kind": r["kind"],
                "answered": r["a_id"] is not None,
                "correct": None if r["a_id"] is None else bool(r["a_correct"]),
                "question": repo.public_question(r, shuffle_seed=lesson["id"]),
            }
            for r in items
        ],
    }


def lesson_size(user: sqlite3.Row) -> int:
    return DEMO_LESSON_SIZE if demo_mode() and user["id"] == "demo" else LESSON_SIZE


def plan(conn: sqlite3.Connection, user: sqlite3.Row, day: str) -> tuple[list[Pick], dict[str, int]]:
    h = history.for_day(conn, user["id"], day)
    picks = build_lesson(repo.ratings(conn, user["id"]), repo.candidates(conn), h,
                         seed=f"{user['id']}:{day}", size=lesson_size(user))
    return picks, h.misses_in_latest_lesson


def create_lesson(conn: sqlite3.Connection, user: sqlite3.Row, day: str) -> sqlite3.Row:
    picks, _ = plan(conn, user, day)
    lid = lesson_id_for(user["id"], day)
    conn.execute("INSERT INTO lessons (id, user_id, date) VALUES (?, ?, ?)", (lid, user["id"], day))
    conn.executemany(
        "INSERT INTO lesson_items (lesson_id, position, question_id, kind) VALUES (?, ?, ?, ?)",
        [(lid, i + 1, p.question_id, p.kind) for i, p in enumerate(picks)],
    )
    return conn.execute("SELECT * FROM lessons WHERE id = ?", (lid,)).fetchone()


@router.get("/lessons/today")
def lessons_today(
    user: sqlite3.Row = Depends(current_user),
    base: date = Depends(client_date),
    conn: sqlite3.Connection = Depends(db.get_conn),
):
    if not user["placed"]:
        raise ApiError(409, "not_placed", "Take the placement test first")
    day = today_for(user, base)
    lesson = conn.execute("SELECT * FROM lessons WHERE user_id = ? AND date = ?", (user["id"], day)).fetchone()
    if lesson is None:
        lesson = create_lesson(conn, user, day)
    return lesson_payload(conn, lesson)


@router.get("/lessons/next/preview")
def next_preview(
    user: sqlite3.Row = Depends(current_user),
    base: date = Depends(client_date),
    conn: sqlite3.Connection = Depends(db.get_conn),
):
    if not user["placed"]:
        raise ApiError(409, "not_placed", "Take the placement test first")
    tomorrow = (date.fromisoformat(today_for(user, base)) + timedelta(days=1)).isoformat()
    picks, misses = plan(conn, user, tomorrow)
    ratings = repo.ratings(conn, user["id"])
    focus: list[str] = []
    for p in picks:
        if p.kind == "focus" and p.topic not in focus:
            focus.append(p.topic)
    return {
        "date": tomorrow,
        "focus_topics": [
            {"topic": t, "reason": "missed_last_lesson" if misses.get(t) else "lowest_rating", "rating": round(ratings[t])}
            for t in focus
        ],
        "items": [
            {"topic": p.topic, "track": p.track, "format": repo.question(conn, p.question_id)["format"],
             "difficulty_rating": round(p.rating), "kind": p.kind}
            for p in picks
        ],
    }
