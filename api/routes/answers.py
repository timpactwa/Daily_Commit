import json
import sqlite3
from datetime import date
from typing import Union

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, StrictInt, StrictStr

from api import db, repo
from api.deps import client_date, current_user, today_for
from api.errors import ApiError, invalid_response, not_found
from engine import elo
from engine.scoring import InvalidResponse, score

router = APIRouter(prefix="/v1")

ResponseValue = Union[StrictInt, StrictStr, list[StrictStr]]


class AnswerIn(BaseModel):
    lesson_id: str
    question_id: str
    response: ResponseValue
    time_ms: int | None = Field(default=None, ge=0)


def record_answer(
    conn: sqlite3.Connection,
    user_id: str,
    qrow: sqlite3.Row,
    response,
    context: elo.Context,
    day: str,
    lesson_id: str | None,
    time_ms: int | None,
) -> tuple[dict, elo.Update]:
    """Grade, update both ratings, and write the attempt. Shared with placement."""
    q = repo.full_question(qrow)
    try:
        s = score(q["format"], response, q["answer"])
    except InvalidResponse as e:
        raise invalid_response(str(e))

    ut = conn.execute(
        "SELECT rating, answers FROM user_topics WHERE user_id = ? AND topic = ?", (user_id, q["topic"])
    ).fetchone()
    u = elo.update(ut["rating"], qrow["live_rating"], s, context, ut["answers"], qrow["attempts"])
    correct = s == 1.0
    lesson_answer = 1 if context == "lesson" else 0

    conn.execute(
        """UPDATE user_topics SET rating = ?, answers = answers + ?, correct = correct + ?
           WHERE user_id = ? AND topic = ?""",
        (u.student_after, lesson_answer, lesson_answer * int(correct), user_id, q["topic"]),
    )
    conn.execute(
        "UPDATE questions SET live_rating = ?, attempts = attempts + 1 WHERE id = ?",
        (u.question_after, q["id"]),
    )
    conn.execute(
        """INSERT INTO attempts (user_id, question_id, lesson_id, context, topic, date, response, score,
                                 correct, time_ms, r_before, r_after, q_before, q_after)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, q["id"], lesson_id, context, q["topic"], day, json.dumps(response), s, int(correct),
         time_ms, u.student_before, u.student_after, u.question_before, u.question_after),
    )
    return q, u


@router.post("/answers")
def submit_answer(
    body: AnswerIn,
    user: sqlite3.Row = Depends(current_user),
    base: date = Depends(client_date),
    conn: sqlite3.Connection = Depends(db.get_conn),
):
    lesson = conn.execute(
        "SELECT * FROM lessons WHERE id = ? AND user_id = ?", (body.lesson_id, user["id"])
    ).fetchone()
    if lesson is None:
        raise not_found("Lesson")
    in_lesson = conn.execute(
        "SELECT 1 FROM lesson_items WHERE lesson_id = ? AND question_id = ?", (lesson["id"], body.question_id)
    ).fetchone()
    qrow = repo.question(conn, body.question_id)
    if in_lesson is None or qrow is None:
        raise not_found("Question")
    if conn.execute(
        "SELECT 1 FROM attempts WHERE lesson_id = ? AND question_id = ?", (lesson["id"], body.question_id)
    ).fetchone():
        raise ApiError(409, "already_answered", "Already answered in this lesson")

    q, u = record_answer(conn, user["id"], qrow, body.response, "lesson",
                         today_for(user, base), lesson["id"], body.time_ms)

    answered, total = conn.execute(
        """SELECT (SELECT COUNT(*) FROM attempts WHERE lesson_id = :l),
                  (SELECT COUNT(*) FROM lesson_items WHERE lesson_id = :l)""",
        {"l": lesson["id"]},
    ).fetchone()
    before, after = round(u.student_before), round(u.student_after)
    out = {
        "correct": u.score == 1.0,
        "score": u.score,
        "correct_answer": q["answer"],
        "explanation": q["explanation"],
        "rating": {"topic": q["topic"], "before": before, "after": after, "delta": after - before},
        "question_rating": {"before": round(u.question_before), "after": round(u.question_after)},
        "lesson_progress": {"answered": answered, "total": total},
    }
    if q.get("provenance"):
        out["provenance"] = q["provenance"]
    return out
