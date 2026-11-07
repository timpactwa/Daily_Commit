"""Build engine.selection.History for a user and a target lesson date."""
import sqlite3
from datetime import date, timedelta

from engine.selection import History

RECENT_DAYS = 3


def for_day(conn: sqlite3.Connection, user_id: str, day: str) -> History:
    since = (date.fromisoformat(day) - timedelta(days=RECENT_DAYS)).isoformat()

    latest = conn.execute(
        "SELECT id FROM lessons WHERE user_id = ? AND date < ? ORDER BY date DESC LIMIT 1", (user_id, day)
    ).fetchone()
    misses: dict[str, int] = {}
    if latest:
        for r in conn.execute(
            "SELECT topic, COUNT(*) AS n FROM attempts WHERE lesson_id = ? AND correct = 0 GROUP BY topic",
            (latest["id"],),
        ):
            misses[r["topic"]] = r["n"]

    answered = {
        r["question_id"]
        for r in conn.execute(
            "SELECT DISTINCT question_id FROM attempts WHERE user_id = ? AND date >= ? AND date < ?",
            (user_id, since, day),
        )
    }
    functions = {
        r["source_function"]
        for r in conn.execute(
            """SELECT DISTINCT q.source_function FROM lesson_items li
               JOIN lessons l ON l.id = li.lesson_id JOIN questions q ON q.id = li.question_id
               WHERE l.user_id = ? AND l.date >= ? AND l.date < ? AND q.source_function IS NOT NULL""",
            (user_id, since, day),
        )
    }
    # Earlier lesson misses not answered correctly since, newest first (spaced review).
    review = [
        r["question_id"]
        for r in conn.execute(
            """SELECT a.question_id, MAX(a.created_at) AS last_miss FROM attempts a
               JOIN questions q ON q.id = a.question_id AND q.active = 1
               WHERE a.user_id = ? AND a.context = 'lesson' AND a.correct = 0 AND a.date < ?
                 AND NOT EXISTS (SELECT 1 FROM attempts b WHERE b.user_id = a.user_id
                                 AND b.question_id = a.question_id AND b.correct = 1 AND b.id > a.id)
               GROUP BY a.question_id ORDER BY last_miss DESC""",
            (user_id, day),
        )
    ]
    return History(misses_in_latest_lesson=misses, recently_answered=answered,
                   recent_functions=functions, review_ids=review)
