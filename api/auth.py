"""Passwords and sessions. Stdlib only: scrypt for passwords, random bearer tokens stored as sha256."""
import hashlib
import hmac
import re
import secrets
import sqlite3

from api import clock

SESSION_DAYS = 30
USERNAME_RE = re.compile(r"^[a-z0-9_]{3,20}$")
RESERVED_PREFIXES = ("sample_", "demo")
MIN_PASSWORD = 8
MAX_PASSWORD = 128
LOGIN_WINDOW_S = 15 * 60
LOGIN_MAX_FAILURES = 10
_N, _R, _P = 2**14, 8, 1


def normalize_username(raw: str) -> str:
    return raw.strip().lower()


def username_problem(username: str) -> str | None:
    if not USERNAME_RE.match(username):
        return "Usernames are 3 to 20 characters: letters, numbers and _"
    if username.startswith(RESERVED_PREFIXES):
        return "That username is reserved"
    return None


def password_problem(password: str) -> str | None:
    if len(password) < MIN_PASSWORD:
        return f"Passwords need at least {MIN_PASSWORD} characters"
    if len(password) > MAX_PASSWORD:
        return f"Passwords can be at most {MAX_PASSWORD} characters"
    return None


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        algo, n, r, p, salt, digest = stored.split("$")
        if algo != "scrypt":
            return False
        test = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=32)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(test.hex(), digest)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(conn: sqlite3.Connection, user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
        (_token_hash(token), user_id, clock.now() + SESSION_DAYS * 86400),
    )
    return token


def session_user(conn: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    return conn.execute(
        """SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
           WHERE s.token_hash = ? AND s.expires_at > ?""",
        (_token_hash(token), clock.now()),
    ).fetchone()


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))


def too_many_failures(conn: sqlite3.Connection, username: str) -> bool:
    since = clock.now() - LOGIN_WINDOW_S
    n = conn.execute("SELECT COUNT(*) FROM login_failures WHERE username = ? AND at >= ?", (username, since)).fetchone()[0]
    return n >= LOGIN_MAX_FAILURES


def record_failure(conn: sqlite3.Connection, username: str) -> None:
    """Call with its own connection: the request's transaction rolls back on the 401."""
    conn.execute("DELETE FROM login_failures WHERE at < ?", (clock.now() - LOGIN_WINDOW_S,))
    conn.execute("INSERT INTO login_failures (username, at) VALUES (?, ?)", (username, clock.now()))
