"""Demo-only endpoints. 404 unless DEMO_MODE=1."""
import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from api import db, seed_demo
from api.deps import client_date, demo_mode, today_for
from api.errors import not_found, unknown_user
from api.routes.users import streak_payload

router = APIRouter(prefix="/v1/demo")


class DemoUser(BaseModel):
    user_id: str = seed_demo.DEMO_ID


def require_demo() -> None:
    if not demo_mode():
        raise not_found("Route")


@router.post("/reset", dependencies=[Depends(require_demo)])
def reset(_: DemoUser | None = None, base: date = Depends(client_date), conn: sqlite3.Connection = Depends(db.get_conn)):
    seed_demo.reset(conn, base.isoformat())
    return {"ok": True}


@router.post("/switch", dependencies=[Depends(require_demo)])
def switch(_: DemoUser | None = None, base: date = Depends(client_date), conn: sqlite3.Connection = Depends(db.get_conn)):
    """Fresh demo user for this run, then hand its id to the app."""
    seed_demo.reset(conn, base.isoformat())
    user = conn.execute("SELECT * FROM users WHERE id = ?", (seed_demo.DEMO_ID,)).fetchone()
    return {
        "user_id": user["id"],
        "display_name": user["display_name"],
        "placed": True,
        "streak": streak_payload(user, base.isoformat()),
    }


@router.post("/advance-day", dependencies=[Depends(require_demo)])
def advance_day(
    x_user_id: str | None = Header(default=None),
    base: date = Depends(client_date),
    conn: sqlite3.Connection = Depends(db.get_conn),
):
    if not x_user_id or conn.execute("SELECT 1 FROM users WHERE id = ?", (x_user_id,)).fetchone() is None:
        raise unknown_user()
    conn.execute("UPDATE users SET day_offset = day_offset + 1 WHERE id = ?", (x_user_id,))
    user = conn.execute("SELECT * FROM users WHERE id = ?", (x_user_id,)).fetchone()
    return {"date": today_for(user, base)}
