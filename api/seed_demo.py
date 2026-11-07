"""Seeded demo user ("Tim on day 7"). Reset on every boot and by the demo endpoints.

Jordan's content/demo/demo-user.json (task P6) overrides the defaults below. Shape:

{
  "display_name": "Tim",
  "streak": {"current": 6, "best": 6},                  # last completed lesson = yesterday
  "ratings": {"caching": 1340, "recursion": 1060, ...},  # any of the 10 topic ids; others stay 1200
  "history": [                                           # optional past answers, oldest first
    {"question_id": "sd-caching-001", "correct": true, "days_ago": 5}
  ]
}

History entries whose question_id is not loaded are skipped. Ratings in `history` are not
replayed; `ratings` is the source of truth and history only feeds the progress sparkline.
"""
import json
import logging
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from api import repo

log = logging.getLogger("demo")
DEMO_ID = "demo"
SEED_FILE = Path(__file__).resolve().parent.parent / "content" / "demo" / "demo-user.json"

DEFAULT = {
    "display_name": "Tim",
    "streak": {"current": 6, "best": 6},
    "ratings": {
        "caching": 1340, "scaling": 1260, "databases": 1190, "async-messaging": 1150, "reliability": 1220,
        "arrays-strings": 1240, "binary-search": 1180, "recursion": 1060, "sorting": 1270, "hash-maps": 1300,
    },
    "history": [],
}


def load_seed() -> dict:
    if SEED_FILE.is_file():
        try:
            return {**DEFAULT, **json.loads(SEED_FILE.read_text(encoding="utf-8"))}
        except (OSError, json.JSONDecodeError) as e:
            log.error("bad %s (%s); using defaults", SEED_FILE, e)
    return DEFAULT


def reset(conn: sqlite3.Connection, today: str) -> None:
    """Recreate the demo user as of `today` (streak alive, last lesson yesterday)."""
    seed = load_seed()
    yesterday = (date.fromisoformat(today) - timedelta(days=1)).isoformat()
    conn.execute("DELETE FROM attempts WHERE user_id = ?", (DEMO_ID,))
    conn.execute("DELETE FROM lesson_items WHERE lesson_id IN (SELECT id FROM lessons WHERE user_id = ?)", (DEMO_ID,))
    conn.execute("DELETE FROM lessons WHERE user_id = ?", (DEMO_ID,))
    conn.execute("DELETE FROM user_topics WHERE user_id = ?", (DEMO_ID,))
    conn.execute("DELETE FROM users WHERE id = ?", (DEMO_ID,))

    streak = seed.get("streak", {})
    current = int(streak.get("current", 6))
    conn.execute(
        """INSERT INTO users (id, display_name, placed, day_offset, streak_current, streak_best, streak_last)
           VALUES (?, ?, 1, 0, ?, ?, ?)""",
        (DEMO_ID, seed.get("display_name", "Tim"), current, max(current, int(streak.get("best", current))), yesterday),
    )
    repo.create_user_topics(conn, DEMO_ID)
    for topic, rating in seed.get("ratings", {}).items():
        if topic in repo.TOPIC_TRACK:
            conn.execute("UPDATE user_topics SET rating = ? WHERE user_id = ? AND topic = ?", (float(rating), DEMO_ID, topic))

    for h in seed.get("history", []):
        q = repo.question(conn, h.get("question_id", ""))
        if q is None:
            continue
        day = (date.fromisoformat(today) - timedelta(days=int(h.get("days_ago", 1)))).isoformat()
        r = conn.execute("SELECT rating FROM user_topics WHERE user_id = ? AND topic = ?", (DEMO_ID, q["topic"])).fetchone()["rating"]
        correct = bool(h.get("correct"))
        conn.execute(
            """INSERT INTO attempts (user_id, question_id, lesson_id, context, topic, date, response, score, correct,
                                     r_before, r_after, q_before, q_after)
               VALUES (?, ?, NULL, 'lesson', ?, ?, 'null', ?, ?, ?, ?, ?, ?)""",
            (DEMO_ID, q["id"], q["topic"], day, float(correct), int(correct), r, r, q["live_rating"], q["live_rating"]),
        )
        conn.execute(
            "UPDATE user_topics SET answers = answers + 1, correct = correct + ? WHERE user_id = ? AND topic = ?",
            (int(correct), DEMO_ID, q["topic"]),
        )
    log.info("demo user reset for %s", today)
