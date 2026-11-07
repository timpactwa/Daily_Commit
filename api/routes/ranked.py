"""Ranked tests: three standardized, timed tests. One attempt per account per tier, ever.

- Start locks the attempt; the server clock is the only clock (the app gets remaining_ms).
- Reopening resumes the same attempt. When time runs out, unanswered questions count as wrong.
- No per-question feedback until the attempt is finished; then a full review.
- Score = correct answers; ties broken by total time (faster first), then by who finished first.
- Answers update the student's topic Elo (one-shot, so a clean signal). Question ratings are
  never changed by ranked answers, so the fixed sets stay comparable.
"""
import json
import sqlite3
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api import clock, db, features, repo
from api.deps import client_date, current_user, today_for
from api.errors import ApiError, invalid_response, not_found
from api.routes.answers import ResponseValue
from engine import elo
from engine.scoring import InvalidResponse, score

router = APIRouter(prefix="/v1/ranked", dependencies=[Depends(features.require("ranked"))])
BOARD_SIZE = 50


class RankedAnswerIn(BaseModel):
    question_id: str
    response: ResponseValue


# ---- helpers ----------------------------------------------------------------

def tiers(conn: sqlite3.Connection) -> list[dict]:
    return [json.loads(r["data"]) for r in conn.execute("SELECT data FROM ranked_tiers ORDER BY position")]


def tier(conn: sqlite3.Connection, tier_id: str) -> dict:
    row = conn.execute("SELECT data FROM ranked_tiers WHERE id = ?", (tier_id,)).fetchone()
    if row is None:
        raise not_found("Ranked test")
    return json.loads(row["data"])


def require_account(user: sqlite3.Row) -> None:
    if user["username"] is None:
        raise ApiError(403, "account_required", "Create an account to take ranked tests")


def get_attempt(conn: sqlite3.Connection, user_id: str, tier_id: str) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM ranked_attempts WHERE user_id = ? AND tier = ?", (user_id, tier_id)).fetchone()
    if row is not None and row["finished_at"] is None and clock.now() >= row["deadline"]:
        row = finish(conn, row)
    return row


def finish(conn: sqlite3.Connection, attempt: sqlite3.Row) -> sqlite3.Row:
    """Close the attempt at now (or at the deadline if it already passed). Unanswered = wrong."""
    end = min(clock.now(), attempt["deadline"])
    correct = conn.execute(
        "SELECT COALESCE(SUM(correct), 0) FROM ranked_answers WHERE attempt_id = ?", (attempt["id"],)
    ).fetchone()[0]
    time_ms = max(0, round((end - attempt["started_at"]) * 1000))
    conn.execute(
        "UPDATE ranked_attempts SET finished_at = ?, score = ?, time_ms = ? WHERE id = ? AND finished_at IS NULL",
        (end, correct, time_ms, attempt["id"]),
    )
    return conn.execute("SELECT * FROM ranked_attempts WHERE id = ?", (attempt["id"],)).fetchone()


def remaining_ms(attempt: sqlite3.Row) -> int:
    return max(0, round((attempt["deadline"] - clock.now()) * 1000))


def standing(conn: sqlite3.Connection, attempt: sqlite3.Row) -> dict:
    """Rank among finished attempts in this tier, and the 'top X%' figure."""
    takers = conn.execute(
        "SELECT COUNT(*) FROM ranked_attempts WHERE tier = ? AND finished_at IS NOT NULL", (attempt["tier"],)
    ).fetchone()[0]
    ahead = conn.execute(
        """SELECT COUNT(*) FROM ranked_attempts WHERE tier = :t AND finished_at IS NOT NULL AND (
               score > :s OR (score = :s AND time_ms < :ms)
               OR (score = :s AND time_ms = :ms AND finished_at < :f))""",
        {"t": attempt["tier"], "s": attempt["score"], "ms": attempt["time_ms"], "f": attempt["finished_at"]},
    ).fetchone()[0]
    rank = ahead + 1
    return {"rank": rank, "takers": takers, "top_percent": max(1, -(-rank * 100 // max(takers, 1)))}


def attempt_summary(conn: sqlite3.Connection, attempt: sqlite3.Row | None) -> dict | None:
    if attempt is None:
        return None
    if attempt["finished_at"] is None:
        answered = conn.execute("SELECT COUNT(*) FROM ranked_answers WHERE attempt_id = ?", (attempt["id"],)).fetchone()[0]
        return {"status": "in_progress", "answered": answered, "total": attempt["total"], "remaining_ms": remaining_ms(attempt)}
    return {"status": "finished", "score": attempt["score"], "total": attempt["total"], "time_ms": attempt["time_ms"],
            **standing(conn, attempt)}


def questions_for(conn: sqlite3.Connection, t: dict) -> list[sqlite3.Row]:
    rows = {r["id"]: r for r in conn.execute(
        f"SELECT * FROM questions WHERE id IN ({','.join('?' * len(t['questions']))})", t["questions"]
    )}
    return [rows[q] for q in t["questions"] if q in rows]


def session(conn: sqlite3.Connection, t: dict, attempt: sqlite3.Row) -> dict:
    """In-progress view: questions in the fixed order (reorder options shuffled the same way for everyone)."""
    answered = {r["question_id"]: json.loads(r["response"]) for r in conn.execute(
        "SELECT question_id, response FROM ranked_answers WHERE attempt_id = ?", (attempt["id"],)
    )}
    return {
        "tier": t["id"], "title": t["title"], "status": "in_progress", "time_limit_s": t["time_limit_s"],
        "remaining_ms": remaining_ms(attempt), "total": attempt["total"],
        "questions": [repo.public_question(r, shuffle_seed=f"ranked:{t['id']}") for r in questions_for(conn, t)],
        "answered": answered,
    }


def suggested_tier(conn: sqlite3.Connection, user_id: str) -> str:
    rs = list(repo.ratings(conn, user_id).values())
    return elo.level(sum(rs) / len(rs)) if rs else "beginner"


# ---- endpoints ---------------------------------------------------------------

@router.get("")
def list_tiers(user: sqlite3.Row = Depends(current_user), conn: sqlite3.Connection = Depends(db.get_conn)):
    suggest = suggested_tier(conn, user["id"])
    out = []
    for t in tiers(conn):
        takers = conn.execute(
            "SELECT COUNT(*) FROM ranked_attempts WHERE tier = ? AND finished_at IS NOT NULL", (t["id"],)
        ).fetchone()[0]
        out.append({
            "id": t["id"], "title": t["title"], "description": t["description"],
            "time_limit_s": t["time_limit_s"], "question_count": len(t["questions"]),
            "suggested": t["id"] == suggest, "takers": takers,
            "attempt": attempt_summary(conn, get_attempt(conn, user["id"], t["id"])),
        })
    return {"has_account": user["username"] is not None, "tiers": out}


@router.post("/{tier_id}/start")
def start(tier_id: str, user: sqlite3.Row = Depends(current_user), conn: sqlite3.Connection = Depends(db.get_conn)):
    """Starts the one attempt, or resumes it if it is still running."""
    t = tier(conn, tier_id)
    require_account(user)
    attempt = get_attempt(conn, user["id"], tier_id)
    if attempt is None:
        now = clock.now()
        conn.execute(
            "INSERT INTO ranked_attempts (user_id, tier, total, started_at, deadline) VALUES (?, ?, ?, ?, ?)",
            (user["id"], tier_id, len(t["questions"]), now, now + t["time_limit_s"]),
        )
        attempt = get_attempt(conn, user["id"], tier_id)
    if attempt["finished_at"] is not None:
        raise ApiError(409, "already_taken", "You already took this ranked test")
    return session(conn, t, attempt)


@router.get("/{tier_id}/attempt")
def resume(tier_id: str, user: sqlite3.Row = Depends(current_user), conn: sqlite3.Connection = Depends(db.get_conn)):
    t = tier(conn, tier_id)
    require_account(user)
    attempt = get_attempt(conn, user["id"], tier_id)
    if attempt is None:
        raise not_found("Attempt")
    if attempt["finished_at"] is not None:
        raise ApiError(409, "already_taken", "You already took this ranked test")
    return session(conn, t, attempt)


@router.post("/{tier_id}/answer")
def answer(
    tier_id: str,
    body: RankedAnswerIn,
    user: sqlite3.Row = Depends(current_user),
    base: date = Depends(client_date),
    conn: sqlite3.Connection = Depends(db.get_conn),
):
    """Saves one answer (final; no feedback until the end) and updates the student's topic Elo."""
    t = tier(conn, tier_id)
    require_account(user)
    attempt = get_attempt(conn, user["id"], tier_id)
    if attempt is None:
        raise not_found("Attempt")
    if attempt["finished_at"] is not None:
        raise ApiError(409, "time_up", "This ranked test is over")
    if body.question_id not in t["questions"]:
        raise not_found("Question")
    if conn.execute(
        "SELECT 1 FROM ranked_answers WHERE attempt_id = ? AND question_id = ?", (attempt["id"], body.question_id)
    ).fetchone():
        raise ApiError(409, "already_answered", "Already answered")

    qrow = repo.question(conn, body.question_id)
    q = repo.full_question(qrow)
    try:
        s = score(q["format"], body.response, q["answer"])
    except InvalidResponse as e:
        raise invalid_response(str(e))
    correct = s == 1.0
    now = clock.now()
    conn.execute(
        "INSERT INTO ranked_answers (attempt_id, question_id, response, correct, answered_at) VALUES (?, ?, ?, ?, ?)",
        (attempt["id"], q["id"], json.dumps(body.response), int(correct), now),
    )

    # Student Elo only (question rating frozen). Counts toward the topic's answer count like a lesson answer.
    ut = conn.execute(
        "SELECT rating, answers FROM user_topics WHERE user_id = ? AND topic = ?", (user["id"], q["topic"])
    ).fetchone()
    u = elo.update(ut["rating"], qrow["live_rating"], s, "lesson", ut["answers"], qrow["attempts"])
    conn.execute(
        "UPDATE user_topics SET rating = ?, answers = answers + 1, correct = correct + ? WHERE user_id = ? AND topic = ?",
        (u.student_after, int(correct), user["id"], q["topic"]),
    )
    conn.execute(
        """INSERT INTO attempts (user_id, question_id, lesson_id, context, topic, date, response, score,
                                 correct, time_ms, r_before, r_after, q_before, q_after)
           VALUES (?, ?, NULL, 'ranked', ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?)""",
        (user["id"], q["id"], q["topic"], today_for(user, base), json.dumps(body.response), s, int(correct),
         u.student_before, u.student_after, qrow["live_rating"], qrow["live_rating"]),
    )
    answered = conn.execute("SELECT COUNT(*) FROM ranked_answers WHERE attempt_id = ?", (attempt["id"],)).fetchone()[0]
    return {"saved": True, "answered": answered, "total": attempt["total"], "remaining_ms": remaining_ms(attempt)}


@router.post("/{tier_id}/submit")
def submit(tier_id: str, user: sqlite3.Row = Depends(current_user), conn: sqlite3.Connection = Depends(db.get_conn)):
    tier(conn, tier_id)
    require_account(user)
    attempt = get_attempt(conn, user["id"], tier_id)
    if attempt is None:
        raise not_found("Attempt")
    if attempt["finished_at"] is None:
        finish(conn, attempt)
    return result(tier_id, user, conn)


@router.get("/{tier_id}/result")
def result(tier_id: str, user: sqlite3.Row = Depends(current_user), conn: sqlite3.Connection = Depends(db.get_conn)):
    """Final score, standing and a full review. Only after the attempt is finished."""
    t = tier(conn, tier_id)
    attempt = get_attempt(conn, user["id"], tier_id)
    if attempt is None:
        raise not_found("Attempt")
    if attempt["finished_at"] is None:
        raise ApiError(409, "not_finished", "Finish the test to see your results")
    answers = {r["question_id"]: r for r in conn.execute(
        "SELECT * FROM ranked_answers WHERE attempt_id = ?", (attempt["id"],)
    )}
    review = []
    for row in questions_for(conn, t):
        q = repo.full_question(row)
        a = answers.get(q["id"])
        review.append({
            "question": repo.public_question(row, shuffle_seed=f"ranked:{t['id']}"),
            "response": json.loads(a["response"]) if a else None,
            "correct": bool(a and a["correct"]),
            "correct_answer": q["answer"],
            "explanation": q["explanation"],
        })
    return {"tier": t["id"], "title": t["title"], **attempt_summary(conn, attempt), "review": review}


@router.get("/{tier_id}/leaderboard")
def leaderboard(tier_id: str, user: sqlite3.Row = Depends(current_user), conn: sqlite3.Connection = Depends(db.get_conn)):
    t = tier(conn, tier_id)
    rows = conn.execute(
        """SELECT a.*, u.username, u.display_name, u.is_sample FROM ranked_attempts a JOIN users u ON u.id = a.user_id
           WHERE a.tier = ? AND a.finished_at IS NOT NULL
           ORDER BY a.score DESC, a.time_ms ASC, a.finished_at ASC""",
        (tier_id,),
    ).fetchall()

    def entry(i: int, r: sqlite3.Row) -> dict:
        return {"rank": i + 1, "username": r["username"] or r["display_name"], "score": r["score"], "total": r["total"],
                "time_ms": r["time_ms"], "sample": bool(r["is_sample"]), "you": r["user_id"] == user["id"]}

    you = next((entry(i, r) for i, r in enumerate(rows) if r["user_id"] == user["id"]), None)
    if you:
        you["top_percent"] = max(1, -(-you["rank"] * 100 // len(rows)))
    return {"tier": t["id"], "title": t["title"], "takers": len(rows),
            "top": [entry(i, r) for i, r in enumerate(rows[:BOARD_SIZE])], "you": you}
