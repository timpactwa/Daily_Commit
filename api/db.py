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
    context     TEXT NOT NULL,                     -- 'placement' | 'lesson'
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
"""


def db_path() -> Path:
    return Path(os.environ.get("DB_PATH", DEFAULT_PATH))


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


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
