"""Queries shared by routes. Keeps SQL out of the route handlers."""
import json
import random
import sqlite3
from pathlib import Path

from engine.elo import R0
from engine.selection import Candidate

ROOT = Path(__file__).resolve().parent.parent
TOPICS = json.loads((ROOT / "contracts" / "topics.json").read_text(encoding="utf-8"))
TOPIC_TRACK = {t["id"]: t["track"] for t in TOPICS["topics"]}
PRIVATE_FIELDS = ("answer", "explanation", "provenance", "placement")


def create_user_topics(conn: sqlite3.Connection, user_id: str) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO user_topics (user_id, topic, rating) VALUES (?, ?, ?)",
        [(user_id, t, R0) for t in TOPIC_TRACK],
    )


def ratings(conn: sqlite3.Connection, user_id: str) -> dict[str, float]:
    rows = conn.execute("SELECT topic, rating FROM user_topics WHERE user_id = ?", (user_id,))
    return {r["topic"]: r["rating"] for r in rows}


def question(conn: sqlite3.Connection, qid: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()


def candidates(conn: sqlite3.Connection, placement_only: bool = False) -> list[Candidate]:
    sql = "SELECT id, topic, track, live_rating, source_function FROM questions WHERE active = 1"
    if placement_only:
        sql += " AND placement = 1"
    return [Candidate(r["id"], r["topic"], r["track"], r["live_rating"], r["source_function"]) for r in conn.execute(sql)]


def public_question(row: sqlite3.Row, shuffle_seed: str = "") -> dict:
    """Question as sent to the app: answer-free, live difficulty, reorder options shuffled."""
    q = json.loads(row["data"])
    for k in PRIVATE_FIELDS:
        q.pop(k, None)
    q["difficulty_rating"] = round(row["live_rating"])
    if q["format"] == "reorder":
        opts = list(q["options"])
        rng = random.Random(f"{shuffle_seed}:{q['id']}")
        original = [o["id"] for o in opts]
        for _ in range(10):  # never hand back the solved order
            rng.shuffle(opts)
            if [o["id"] for o in opts] != original:
                break
        q["options"] = opts
    return q


def full_question(row: sqlite3.Row) -> dict:
    return json.loads(row["data"])
