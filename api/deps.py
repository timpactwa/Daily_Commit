"""Request-scoped helpers: current user and the user's "today"."""
import os
import re
import sqlite3
from datetime import date, datetime, timedelta, timezone

from fastapi import Depends, Header

from api import auth, db
from api.errors import ApiError, unknown_user

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def demo_mode() -> bool:
    return os.environ.get("DEMO_MODE", "0") in ("1", "true", "yes")


def bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return None


def current_user(
    x_user_id: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    conn: sqlite3.Connection = Depends(db.get_conn),
) -> sqlite3.Row:
    """Accounts authenticate with `Authorization: Bearer <token>`. Guests (no password) keep
    using `X-User-Id`. An account's id alone is never enough: that would bypass the password."""
    token = bearer_token(authorization)
    if token:
        row = auth.session_user(conn, token)
        if row is None:
            raise ApiError(401, "session_expired", "Your session expired. Sign in again.")
        return row
    if not x_user_id:
        raise unknown_user()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (x_user_id,)).fetchone()
    if row is None:
        raise unknown_user()
    if row["password_hash"]:
        raise ApiError(401, "session_expired", "Sign in to continue.")
    return row


def client_date(x_client_date: str | None = Header(default=None)) -> date:
    if x_client_date and DATE_RE.match(x_client_date):
        try:
            return date.fromisoformat(x_client_date)
        except ValueError:
            pass
    return datetime.now(timezone.utc).date()


def today_for(user: sqlite3.Row, base: date) -> str:
    """User's effective today as YYYY-MM-DD (demo day offset applied only in DEMO_MODE)."""
    offset = user["day_offset"] if demo_mode() else 0
    return (base + timedelta(days=offset)).isoformat()
