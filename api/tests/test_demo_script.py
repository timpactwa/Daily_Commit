"""The live demo, beat by beat, through the API (docs/PLAN.md "Demo flow mapping").

If this test fails, the demo is broken. Uses a realistic content set and DEMO_MODE=1.
"""
import pytest
from fastapi.testclient import TestClient

from api import content_loader
from api.tests.test_lesson_selection_api import make_content

DAY = "2026-11-08"


@pytest.fixture()
def demo(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "demo.db"))
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setattr(content_loader, "CONTENT", make_content(tmp_path))
    from api.main import app

    with TestClient(app) as c:
        yield c


def answer(q, right=True):
    if q["format"] == "mcq":
        return "a" if right else "b"
    return 2 if right else 1


def test_demo_script(demo):
    # Beat 2: fresh user takes a 4-question placement (2 per track); levels spread out.
    me = demo.post("/v1/users", json={"display_name": "Judge"}).json()
    h = {"X-User-Id": me["user_id"], "X-Client-Date": DAY}
    qs = demo.get("/v1/placement?limit=4", headers=h).json()["questions"]
    assert len(qs) == 4 and {q["track"] for q in qs} == {"system-design", "debugging"}
    res = demo.post("/v1/placement", headers=h, json={"responses": [
        {"question_id": q["id"], "response": answer(q, right=i % 2 == 0)} for i, q in enumerate(qs)]}).json()
    assert len({t["rating"] for t in res["topics"]}) >= 4, "starting levels should not look copy-pasted"

    # Beat 3: switch to the day-7 user.
    d = demo.post("/v1/demo/switch", headers={"X-Client-Date": DAY}, json={"user_id": "demo"}).json()
    assert d["streak"]["current"] == 6
    h = {"X-User-Id": "demo", "X-Client-Date": DAY}

    # Beat 4: 3-item lesson with an SD question and a tap-the-line question.
    lesson = demo.get("/v1/lessons/today", headers=h).json()
    items = [i["question"] for i in lesson["items"]]
    assert len(items) == 3
    assert {"mcq", "tap_line"} <= {q["format"] for q in items}

    # Beat 5: answer one right, miss one on purpose, preview shows the missed topic.
    sd = next(q for q in items if q["track"] == "system-design")
    dbg = next(q for q in items if q["format"] == "tap_line")
    r1 = demo.post("/v1/answers", headers=h, json={"lesson_id": lesson["lesson_id"], "question_id": sd["id"], "response": answer(sd)}).json()
    r2 = demo.post("/v1/answers", headers=h, json={"lesson_id": lesson["lesson_id"], "question_id": dbg["id"], "response": answer(dbg, False)}).json()
    assert r1["correct"] and r1["rating"]["delta"] > 0
    assert not r2["correct"] and r2["rating"]["delta"] < 0 and r2["provenance"]["mutated_line"]
    preview = demo.get("/v1/lessons/next/preview", headers=h).json()
    shifted = [f for f in preview["focus_topics"] if f["topic"] == dbg["topic"]]
    assert shifted and shifted[0]["reason"] == "missed_last_lesson"

    # Beat 6: finish the lesson, streak 6 -> 7.
    rest = [q for q in items if q["id"] not in (sd["id"], dbg["id"])]
    for q in rest:
        demo.post("/v1/answers", headers=h, json={"lesson_id": lesson["lesson_id"], "question_id": q["id"], "response": answer(q)})
    done = demo.post(f"/v1/lessons/{lesson['lesson_id']}/complete", headers=h).json()
    assert done["streak"]["current"] == 7 and done["streak"]["extended"]

    # Progress screen has data for every topic.
    p = demo.get("/v1/progress", headers=h).json()
    assert len(p["topics"]) == 10 and p["streak"]["today_done"]

    # Rehearsal again: switch resets cleanly.
    again = demo.post("/v1/demo/switch", headers={"X-Client-Date": DAY}, json={"user_id": "demo"}).json()
    assert again["streak"] == {"current": 6, "best": 6, "today_done": False}
