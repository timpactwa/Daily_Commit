import secrets
import sqlite3
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api import db, repo
from api.deps import client_date, current_user, today_for

router = APIRouter(prefix="/v1")


class NewUser(BaseModel):
    display_name: str = Field(default="Student", max_length=40)


def streak_payload(user: sqlite3.Row, today: str) -> dict:
    return {
        "current": user["streak_current"],
        "best": user["streak_best"],
        "today_done": user["streak_last"] == today,
    }


@router.get("/topics")
def topics():
    return repo.TOPICS


@router.post("/users", status_code=201)
def create_user(body: NewUser | None = None, conn: sqlite3.Connection = Depends(db.get_conn)):
    name = (body.display_name if body else "Student").strip() or "Student"
    user_id = "u_" + secrets.token_hex(4)
    conn.execute("INSERT INTO users (id, display_name) VALUES (?, ?)", (user_id, name))
    repo.create_user_topics(conn, user_id)
    return {"user_id": user_id, "display_name": name, "placed": False}


@router.get("/me")
def me(user: sqlite3.Row = Depends(current_user), base: date = Depends(client_date)):
    return {
        "user_id": user["id"],
        "display_name": user["display_name"],
        "placed": bool(user["placed"]),
        "streak": streak_payload(user, today_for(user, base)),
    }
