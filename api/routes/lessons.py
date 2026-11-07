import sqlite3
from datetime import date, timedelta

from fastapi import APIRouter, Depends

from api import db, history, repo
from api.deps import client_date, current_user, demo_mode, today_for
from api.errors import ApiError, not_found
from api.routes.users import user_streak
from engine import streak as streaks
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


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(
    lesson_id: str,
    user: sqlite3.Row = Depends(current_user),
    base: date = Depends(client_date),
    conn: sqlite3.Connection = Depends(db.get_conn),
):
    lesson = conn.execute("SELECT * FROM lessons WHERE id = ? AND user_id = ?", (lesson_id, user["id"])).fetchone()
    if lesson is None:
        raise not_found("Lesson")
    day = today_for(user, base)

    # Streak counts the day the lesson is completed (idempotent for repeat calls).
    new, extended = streaks.complete(user_streak(user), day)
    conn.execute(
        "UPDATE users SET streak_current = ?, streak_best = ?, streak_last = ? WHERE id = ?",
        (new.current, new.best, new.last, user["id"]),
    )
    conn.execute("UPDATE lessons SET status = 'completed' WHERE id = ?", (lesson_id,))

    attempts = conn.execute(
        "SELECT topic, correct, r_before, r_after FROM attempts WHERE lesson_id = ? ORDER BY id", (lesson_id,)
    ).fetchall()
    changes: dict[str, list[float]] = {}
    for a in attempts:
        changes.setdefault(a["topic"], [a["r_before"], a["r_after"]])[1] = a["r_after"]
    return {
        "summary": {"correct": sum(a["correct"] for a in attempts), "total": len(attempts)},
        "rating_changes": [{"topic": t, "before": round(b), "after": round(a)} for t, (b, a) in changes.items()],
        "streak": {"current": new.current, "best": new.best, "today_done": True, "extended": extended},
    }
