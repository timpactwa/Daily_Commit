"""Lesson selection through the API with a realistic content set (10 topics x 8 questions)."""
import json

import pytest
from fastapi.testclient import TestClient

from api import content_loader, repo


def make_content(tmp_path):
    qs = []
    for topic, track in repo.TOPIC_TRACK.items():
        for i in range(8):
            base = {"version": 1, "track": track, "topic": topic, "explanation": "x",
                    "difficulty_rating": 900 + 80 * i, "placement": i in (1, 4, 6)}
            if track == "system-design":
                qs.append({**base, "id": f"sd-{topic}-{i}", "format": "mcq", "prompt": "?",
                           "options": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}], "answer": "a"})
            else:
                fn = f"pipeline/corpus/{topic}.py::f{i // 2}"
                qs.append({**base, "id": f"dbg-{topic}-{i}", "format": "tap_line", "prompt": "Tap",
                           "code": "def f(x):\n    y = x + 1\n    return y", "test_output": "f(1): expected 3, got 2",
                           "answer": 2, "provenance": {"source_function": fn, "mutation_operator": "off_by_one",
                                                       "original_line": "    y = x + 2", "mutated_line": "    y = x + 1",
                                                       "tests_failed": 1, "tests_total": 3}})
    d = tmp_path / "content" / "gen"
    d.mkdir(parents=True)
    (d / "questions.json").write_text(json.dumps(qs))
    return tmp_path / "content"


@pytest.fixture()
def big(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setattr(content_loader, "CONTENT", make_content(tmp_path))
    from api.main import app

    with TestClient(app) as c:
        yield c


def placed(client, day="2026-11-08"):
    uid = client.post("/v1/users", json={}).json()["user_id"]
    h = {"X-User-Id": uid, "X-Client-Date": day}
    qs = client.get("/v1/placement", headers=h).json()["questions"]
    assert len(qs) == 10
    client.post("/v1/placement", headers=h, json={"responses": [
        {"question_id": q["id"], "response": "a" if q["format"] == "mcq" else 2} for q in qs]})
    return h


def wrong(q):
    return "b" if q["format"] == "mcq" else 1


def test_full_lesson_shape(big):
    h = placed(big)
    lesson = big.get("/v1/lessons/today", headers=h).json()
    assert len(lesson["items"]) == 6
    assert {i["question"]["track"] for i in lesson["items"]} == {"system-design", "debugging"}
    assert lesson["items"][-1]["kind"] == "mix"
    fns = [i["question"]["id"] for i in lesson["items"] if i["question"]["track"] == "debugging"]
    assert len({f.rsplit("-", 1)[0] + str(int(f.rsplit("-", 1)[1]) // 2) for f in fns}) == len(fns)


def test_miss_mid_lesson_shifts_preview(big):
    h = placed(big)
    lesson = big.get("/v1/lessons/today", headers=h).json()
    focus_today = set(lesson["focus_topics"])
    target = next(i["question"] for i in lesson["items"] if i["question"]["topic"] not in focus_today)
    r = big.post("/v1/answers", headers=h, json={"lesson_id": lesson["lesson_id"], "question_id": target["id"],
                                                  "response": wrong(target)})
    assert r.json()["correct"] is False

    preview = big.get("/v1/lessons/next/preview", headers=h).json()
    assert preview["date"] == "2026-11-09"
    missed = [f for f in preview["focus_topics"] if f["topic"] == target["topic"]]
    assert missed and missed[0]["reason"] == "missed_last_lesson"


def test_tomorrow_avoids_todays_questions(big):
    h = placed(big)
    lesson = big.get("/v1/lessons/today", headers=h).json()
    for item in lesson["items"]:
        q = item["question"]
        big.post("/v1/answers", headers=h, json={"lesson_id": lesson["lesson_id"], "question_id": q["id"], "response": wrong(q)})
    tomorrow = big.get("/v1/lessons/today", headers={**h, "X-Client-Date": "2026-11-09"}).json()
    today_ids = {i["question"]["id"] for i in lesson["items"]}
    new_ids = {i["question"]["id"] for i in tomorrow["items"] if i["kind"] != "review"}
    assert not today_ids & new_ids
    assert any(i["kind"] == "review" and i["question"]["id"] in today_ids for i in tomorrow["items"])


def test_demo_user_gets_three_items(big, monkeypatch):
    from api import db

    monkeypatch.setenv("DEMO_MODE", "1")
    with db.transaction() as conn:
        conn.execute("INSERT INTO users (id, display_name, placed) VALUES ('demo', 'Tim', 1)")
        repo.create_user_topics(conn, "demo")
    lesson = big.get("/v1/lessons/today", headers={"X-User-Id": "demo", "X-Client-Date": "2026-11-08"}).json()
    assert len(lesson["items"]) == 3


def test_complete_lesson_and_streak(big):
    h = placed(big)
    lesson = big.get("/v1/lessons/today", headers=h).json()
    for item in lesson["items"][:3]:
        q = item["question"]
        big.post("/v1/answers", headers=h, json={"lesson_id": lesson["lesson_id"], "question_id": q["id"],
                                                  "response": "a" if q["format"] == "mcq" else 2})
    r = big.post(f"/v1/lessons/{lesson['lesson_id']}/complete", headers=h).json()
    assert r["summary"] == {"correct": 3, "total": 3}
    assert r["streak"] == {"current": 1, "best": 1, "today_done": True, "extended": True}
    assert all(c["after"] > c["before"] for c in r["rating_changes"])
    again = big.post(f"/v1/lessons/{lesson['lesson_id']}/complete", headers=h).json()
    assert again["streak"]["extended"] is False and again["streak"]["current"] == 1
    assert big.get("/v1/lessons/today", headers=h).json()["status"] == "completed"
    assert big.get("/v1/me", headers=h).json()["streak"]["today_done"] is True

    h2 = {**h, "X-Client-Date": "2026-11-09"}
    l2 = big.get("/v1/lessons/today", headers=h2).json()
    assert big.post(f"/v1/lessons/{l2['lesson_id']}/complete", headers=h2).json()["streak"]["current"] == 2
    gone = big.get("/v1/me", headers={**h, "X-Client-Date": "2026-11-12"}).json()["streak"]
    assert gone == {"current": 0, "best": 2, "today_done": False}


def test_complete_unknown_lesson(big):
    h = placed(big)
    assert big.post("/v1/lessons/l_nope/complete", headers=h).status_code == 404
