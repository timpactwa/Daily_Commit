"""DEMO_MODE only: labeled sample players so the ranked leaderboards are not empty on stage.

Every sample user has username sample_user_NN, is_sample = 1, and no password (cannot sign in).
The app shows a "sample" tag next to them. Deterministic: the same boards on every boot.
"""
import json
import logging
import random
import sqlite3

from api import clock, repo

log = logging.getLogger("demo")
SAMPLE_USERS = 24
# Chance of answering each question correctly, per tier (a spread of skill levels around it).
TIER_SKILL = {"beginner": 0.78, "intermediate": 0.6, "advanced": 0.42}


def seed(conn: sqlite3.Connection) -> int:
    conn.execute("DELETE FROM users WHERE is_sample = 1")
    tier_rows = [dict(r) for r in conn.execute("SELECT id, data FROM ranked_tiers ORDER BY position")]
    if not tier_rows:
        return 0


    now = clock.now()
    for i in range(1, SAMPLE_USERS + 1):
        uid = f"sample_{i:02d}"
        conn.execute(
            "INSERT INTO users (id, display_name, placed, username, is_sample) VALUES (?, ?, 1, ?, 1)",
            (uid, f"Sample user {i:02d}", f"sample_user_{i:02d}"),
        )
        repo.create_user_topics(conn, uid)
        rng = random.Random(f"sample:{i}")
        skill_shift = rng.uniform(-0.2, 0.2)
        for t in tier_rows:
            tier = json.loads(t["data"])
            total = len(tier["questions"])
            p = min(0.97, max(0.05, TIER_SKILL.get(tier["id"], 0.6) + skill_shift))
            score = sum(rng.random() < p for _ in range(total))
            limit = tier["time_limit_s"]
            time_s = rng.uniform(0.4, 0.97) * limit
            started = now - rng.uniform(1, 72) * 3600
            conn.execute(
                """INSERT INTO ranked_attempts (user_id, tier, total, started_at, deadline, finished_at, score, time_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid, tier["id"], total, started, started + limit, started + time_s, score, round(time_s * 1000)),
            )
    log.info("seeded %d labeled sample players", SAMPLE_USERS)
    return SAMPLE_USERS
