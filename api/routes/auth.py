"""Accounts: signup (claims the current guest's progress), login, logout."""
import secrets
import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from api import auth, db, features, repo, seed_demo
from api.deps import bearer_token, client_date, today_for
from api.errors import ApiError, invalid_response
from api.routes.users import me_payload

router = APIRouter(prefix="/v1/auth", dependencies=[Depends(features.require("accounts"))])


class SignupIn(BaseModel):
    username: str = Field(max_length=40)
    password: str = Field(max_length=200)
    display_name: str | None = Field(default=None, max_length=40)


class LoginIn(BaseModel):
    username: str = Field(max_length=40)
    password: str = Field(max_length=200)


def claimable_guest(conn: sqlite3.Connection, x_user_id: str | None) -> sqlite3.Row | None:
    """The guest whose progress a new account takes over. Never the shared demo user or a sample."""
    if not x_user_id or x_user_id == seed_demo.DEMO_ID:
        return None
    row = conn.execute("SELECT * FROM users WHERE id = ?", (x_user_id,)).fetchone()
    if row is None or row["username"] is not None or row["password_hash"] or row["is_sample"]:
        return None
    return row


@router.post("/signup", status_code=201)
def signup(
    body: SignupIn,
    x_user_id: str | None = Header(default=None),
    base: date = Depends(client_date),
    conn: sqlite3.Connection = Depends(db.get_conn),
):
    username = auth.normalize_username(body.username)
    problem = auth.username_problem(username) or auth.password_problem(body.password)
    if problem:
        raise invalid_response(problem)
    if conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        raise ApiError(409, "username_taken", "That username is taken")

    pw = auth.hash_password(body.password)
    guest = claimable_guest(conn, x_user_id)
    name = (body.display_name or "").strip()
    if guest is not None:
        conn.execute(
            "UPDATE users SET username = ?, password_hash = ?, display_name = COALESCE(NULLIF(?, ''), display_name) WHERE id = ?",
            (username, pw, name, guest["id"]),
        )
        user_id = guest["id"]
    else:
        user_id = "u_" + secrets.token_hex(4)
        conn.execute(
            "INSERT INTO users (id, display_name, username, password_hash) VALUES (?, ?, ?, ?)",
            (user_id, name or username, username, pw),
        )
        repo.create_user_topics(conn, user_id)
    token = auth.create_session(conn, user_id)
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return {"token": token, "claimed_guest": guest is not None, "user": me_payload(user, today_for(user, base))}


@router.post("/login")
def login(body: LoginIn, base: date = Depends(client_date), conn: sqlite3.Connection = Depends(db.get_conn)):
    username = auth.normalize_username(body.username)
    if auth.too_many_failures(conn, username):
        raise ApiError(429, "too_many_attempts", "Too many failed sign-ins. Try again in 15 minutes.")
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user is None or not auth.verify_password(body.password, user["password_hash"]):
        with db.transaction() as failures:
            auth.record_failure(failures, username)
        raise ApiError(401, "bad_credentials", "Wrong username or password")
    token = auth.create_session(conn, user["id"])
    return {"token": token, "user": me_payload(user, today_for(user, base))}


@router.post("/logout")
def logout(authorization: str | None = Header(default=None), conn: sqlite3.Connection = Depends(db.get_conn)):
    token = bearer_token(authorization)
    if token:
        auth.delete_session(conn, token)
    return {"ok": True}
