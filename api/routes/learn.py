"""Learning modules: read a topic, pass each section's checkpoint to unlock the next.

Completion only; checkpoints never change Elo (retries make them a poor skill signal).
"""
import json
import sqlite3

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, StrictStr

from api import db, features
from api.deps import current_user
from api.errors import ApiError, invalid_response, not_found

router = APIRouter(prefix="/v1/learn", dependencies=[Depends(features.require("learn"))])


class CheckIn(BaseModel):
    section_id: str = Field(max_length=60)
    response: StrictStr = Field(max_length=4)


def module(conn: sqlite3.Connection, topic: str) -> dict:
    row = conn.execute("SELECT data FROM learn_modules WHERE topic = ?", (topic,)).fetchone()
    if row is None:
        raise not_found("Module")
    return json.loads(row["data"])


def passed(conn: sqlite3.Connection, user_id: str, topic: str) -> set[str]:
    return {r["section_id"] for r in conn.execute(
        "SELECT section_id FROM learn_progress WHERE user_id = ? AND topic = ?", (user_id, topic)
    )}


def progress_fields(m: dict, done: set[str]) -> dict:
    ids = [s["id"] for s in m["sections"]]
    n = sum(1 for i in ids if i in done)
    return {"passed": [i for i in ids if i in done], "sections": len(ids), "completed": n == len(ids)}


@router.get("")
def list_modules(user: sqlite3.Row = Depends(current_user), conn: sqlite3.Connection = Depends(db.get_conn)):
    out = []
    for r in conn.execute("SELECT data FROM learn_modules ORDER BY position"):
        m = json.loads(r["data"])
        p = progress_fields(m, passed(conn, user["id"], m["topic"]))
        out.append({
            "topic": m["topic"], "track": m["track"], "title": m["title"], "summary": m["summary"],
            "minutes": m["minutes"], "sections": p["sections"], "passed": len(p["passed"]), "completed": p["completed"],
        })
    return {"modules": out}


@router.get("/{topic}")
def get_module(topic: str, user: sqlite3.Row = Depends(current_user), conn: sqlite3.Connection = Depends(db.get_conn)):
    """The whole module minus checkpoint answers and explanations (those come back from /check)."""
    m = module(conn, topic)
    sections = []
    for s in m["sections"]:
        check = {k: v for k, v in s["check"].items() if k not in ("answer", "explanation")}
        sections.append({**s, "check": check})
    return {**m, "sections": sections, "progress": progress_fields(m, passed(conn, user["id"], topic))}


@router.post("/{topic}/check")
def check(topic: str, body: CheckIn, user: sqlite3.Row = Depends(current_user), conn: sqlite3.Connection = Depends(db.get_conn)):
    """Grade one checkpoint. Wrong answers can retry; the explanation is returned once correct.
    A section unlocks only after every earlier section is passed."""
    m = module(conn, topic)
    ids = [s["id"] for s in m["sections"]]
    if body.section_id not in ids:
        raise not_found("Section")
    sec = m["sections"][ids.index(body.section_id)]
    if body.response not in {o["id"] for o in sec["check"]["options"]}:
        raise invalid_response("Unknown option")
    done = passed(conn, user["id"], topic)
    if any(i not in done for i in ids[: ids.index(body.section_id)]):
        raise ApiError(409, "locked", "Finish the earlier sections first")

    correct = body.response == sec["check"]["answer"]
    if correct:
        conn.execute(
            "INSERT OR IGNORE INTO learn_progress (user_id, topic, section_id) VALUES (?, ?, ?)",
            (user["id"], topic, body.section_id),
        )
        done.add(body.section_id)
    out = {"correct": correct, **progress_fields(m, done)}
    if correct:
        out["explanation"] = sec["check"]["explanation"]
    return out
