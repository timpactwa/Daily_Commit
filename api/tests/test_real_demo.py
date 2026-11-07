"""The live demo against the REAL content and REAL demo seed, across many dates.

test_demo_script.py proves the flow with synthetic content; this proves the actual bank and
seed deliver every beat no matter which day the demo happens to run on.
"""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from api import content_loader, repo

pytestmark = pytest.mark.skipif(
    not (content_loader.CONTENT / "debugging").is_dir() or not (content_loader.CONTENT / "system-design").is_dir(),
    reason="needs both content tracks",
)


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    mp.setenv("DB_PATH", str(tmp_path_factory.mktemp("real") / "demo.db"))
    mp.setenv("DEMO_MODE", "1")
    from api.main import app

    with TestClient(app) as c:
        yield c
    mp.undo()


def wrong(q):
    return {"mcq": "zz", "tap_node": "zz", "tap_line": 999}.get(q["format"], [o["id"] for o in q.get("options", [])][::-1])


def right_answer(conn, qid):
    return repo.full_question(repo.question(conn, qid))["answer"]


@pytest.mark.parametrize("offset", range(30))
def test_every_beat_on_any_day(client, offset):
    from api import db

    day = (date(2026, 11, 8) + timedelta(days=offset)).isoformat()

    # Placement (fresh user, 4 questions): both tracks, levels spread.
    uid = client.post("/v1/users", json={"display_name": "Judge"}).json()["user_id"]
    h0 = {"X-User-Id": uid, "X-Client-Date": day}
    qs = client.get("/v1/placement?limit=4", headers=h0).json()["questions"]
    assert len(qs) == 4 and {q["track"] for q in qs} == {"system-design", "debugging"}

    # Switch to day-7 user.
    sw = client.post("/v1/demo/switch", headers={"X-Client-Date": day}, json={"user_id": "demo"}).json()
    assert sw["streak"]["current"] == 6
    h = {"X-User-Id": "demo", "X-Client-Date": day}

    # Lesson: 3 items, has a system design question and a tap-the-line question; Q3 is the mix item.
    lesson = client.get("/v1/lessons/today", headers=h).json()
    items = [i for i in lesson["items"]]
    assert len(items) == 3
    assert any(i["question"]["track"] == "system-design" for i in items)
    assert any(i["question"]["format"] == "tap_line" for i in items)
    assert items[2]["kind"] == "mix"

    # Answer Q1 and Q2 correctly, miss Q3 on purpose.
    with db.transaction() as conn:
        answers = [right_answer(conn, i["question"]["id"]) for i in items[:2]]
    for item, ans in zip(items[:2], answers):
        r = client.post("/v1/answers", headers=h, json={"lesson_id": lesson["lesson_id"], "question_id": item["question"]["id"], "response": ans}).json()
        assert r["correct"] is True
    q3 = items[2]["question"]
    r3 = client.post("/v1/answers", headers=h, json={"lesson_id": lesson["lesson_id"], "question_id": q3["id"], "response": wrong(q3)}).json()
    assert r3["correct"] is False

    # Tomorrow shifts toward Q3's topic.
    preview = client.get("/v1/lessons/next/preview", headers=h).json()
    focus = {f["topic"]: f["reason"] for f in preview["focus_topics"]}
    assert focus.get(q3["topic"]) == "missed_last_lesson", (day, q3["topic"], focus)

    # Streak 6 -> 7.
    done = client.post(f"/v1/lessons/{lesson['lesson_id']}/complete", headers=h).json()
    assert done["streak"]["current"] == 7
