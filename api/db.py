"""SQLite storage. One connection per request; all schema lives here.

DB_PATH env var overrides the location (Railway mounts a volume; tests use a temp file).
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_PATH = Path(__file__).resolve().parent / "data" / "app.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id             TEXT PRIMARY KEY,
    display_name   TEXT NOT NULL,
    placed         INTEGER NOT NULL DEFAULT 0,
    day_offset     INTEGER NOT NULL DEFAULT 0,     -- demo mode: shifts "today"
    streak_current INTEGER NOT NULL DEFAULT 0,
    streak_best    INTEGER NOT NULL DEFAULT 0,
    streak_last    TEXT,                           -- YYYY-MM-DD of last completed lesson
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_topics (
    user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic    TEXT NOT NULL,
    rating   REAL NOT NULL,
    answers  INTEGER NOT NULL DEFAULT 0,           -- rated lesson answers (drives K_NEW vs K_SETTLED)
    correct  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, topic)
);

CREATE TABLE IF NOT EXISTS questions (
    id              TEXT PRIMARY KEY,
    track           TEXT NOT NULL,
    topic           TEXT NOT NULL,
    format          TEXT NOT NULL,
    data            TEXT NOT NULL,                 -- full question JSON from /content
    seed_rating     REAL NOT NULL,
    live_rating     REAL NOT NULL,                 -- learned; never reset by reloads
    attempts        INTEGER NOT NULL DEFAULT 0,
    source_function TEXT,                          -- debugging: provenance.source_function
    placement       INTEGER NOT NULL DEFAULT 0,
    active          INTEGER NOT NULL DEFAULT 1     -- 0 when removed from /content
);
CREATE INDEX IF NOT EXISTS questions_topic ON questions(topic, active);

CREATE TABLE IF NOT EXISTS lessons (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'in_progress',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, date)
);

CREATE TABLE IF NOT EXISTS lesson_items (
    lesson_id   TEXT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    question_id TEXT NOT NULL REFERENCES questions(id),
    kind        TEXT NOT NULL,
    PRIMARY KEY (lesson_id, position)
);

CREATE TABLE IF NOT EXISTS attempts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL REFERENCES questions(id),
    lesson_id   TEXT,                              -- NULL for placement
    context     TEXT NOT NULL,                     -- 'placement' | 'lesson' | 'ranked'
    topic       TEXT NOT NULL,
    date        TEXT NOT NULL,                     -- user's local date when answered
    response    TEXT NOT NULL,                     -- JSON
    score       REAL NOT NULL,
    correct     INTEGER NOT NULL,
    time_ms     INTEGER,
    r_before    REAL NOT NULL,
    r_after     REAL NOT NULL,
    q_before    REAL NOT NULL,
    q_after     REAL NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS attempts_user ON attempts(user_id, created_at);
CREATE INDEX IF NOT EXISTS attempts_lesson ON attempts(lesson_id, question_id);

-- Accounts: a guest row becomes an account when it gets a username + password.
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,                   -- sha256 of the bearer token; the token itself is never stored
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at REAL NOT NULL,                      -- epoch seconds
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS login_failures (
    username TEXT NOT NULL,
    at       REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS login_failures_user ON login_failures(username, at);

-- Learning modules (content/learn) and the reader's passed checkpoints.
CREATE TABLE IF NOT EXISTS learn_modules (
    topic    TEXT PRIMARY KEY,
    position INTEGER NOT NULL,
    data     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS learn_progress (
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic      TEXT NOT NULL,
    section_id TEXT NOT NULL,
    passed_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, topic, section_id)
);

-- Ranked tests (content/ranked/tests.json): one attempt per user per tier, ever.
CREATE TABLE IF NOT EXISTS ranked_tiers (
    id       TEXT PRIMARY KEY,
    position INTEGER NOT NULL,
    data     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ranked_attempts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier        TEXT NOT NULL,
    total       INTEGER NOT NULL,
    started_at  REAL NOT NULL,                     -- epoch seconds, server clock
    deadline    REAL NOT NULL,
    finished_at REAL,                              -- NULL while in progress
    score       INTEGER,                           -- correct answers, set when finished
    time_ms     INTEGER,                           -- min(finish, deadline) - start
    UNIQUE (user_id, tier)
);
CREATE INDEX IF NOT EXISTS ranked_board ON ranked_attempts(tier, finished_at);

CREATE TABLE IF NOT EXISTS ranked_answers (
    attempt_id  INTEGER NOT NULL REFERENCES ranked_attempts(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    response    TEXT NOT NULL,                     -- JSON
    correct     INTEGER NOT NULL,
    answered_at REAL NOT NULL,
    PRIMARY KEY (attempt_id, question_id)
);
"""

# Columns added after the first deploy. ALTER TABLE keeps existing Railway databases working.
MIGRATIONS = [
    ("users", "username", "TEXT"),                 # lowercase; NULL for guests
    ("users", "password_hash", "TEXT"),            # NULL for guests and sample users
    ("users", "is_sample", "INTEGER NOT NULL DEFAULT 0"),
    ("questions", "pool", "TEXT NOT NULL DEFAULT 'lesson'"),  # 'lesson' | 'ranked'
]
POST_MIGRATION = """
CREATE UNIQUE INDEX IF NOT EXISTS users_username ON users(username);
CREATE INDEX IF NOT EXISTS questions_pool ON questions(pool, active);
"""


def db_path() -> Path:
    return Path(os.environ.get("DB_PATH", DEFAULT_PATH))


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # FastAPI may open a request's connection in one worker thread and use or close it in
    # another (sync dependency vs sync endpoint). Each connection still belongs to exactly one
    # request and is used sequentially, so cross-thread use is safe.
    conn = sqlite3.connect(path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init() -> None:
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        for table, column, decl in MIGRATIONS:
            cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
            if column not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
        conn.executescript(POST_MIGRATION)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    """Commit on success, roll back on error, always close."""
    conn = connect()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def get_conn() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: one connection per request, committed if the handler succeeds."""
    with transaction() as conn:
        yield conn
