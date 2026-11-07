"""Accounts, learning modules and ranked tests against a synthetic content tree."""
import copy
import json

import pytest
from fastapi.testclient import TestClient

from api import clock

ROOT_EXAMPLES = json.load(open("contracts/examples/questions.json", encoding="utf-8"))
MCQ = next(q for q in ROOT_EXAMPLES if q["id"] == "sd-caching-001")
TAP = next(q for q in ROOT_EXAMPLES if q["format"] == "tap_line")
BANDS = {"beginner": (600, 1000, 900), "intermediate": (1000, 1300, 1150), "advanced": (1300, 2201, 1400)}


def ranked_content() -> tuple[list[dict], dict]:
    questions, tiers = [], []
    for tier, (lo, hi, rating) in BANDS.items():
        ids = []
        for i in range(5):
            sd = {**copy.deepcopy(MCQ), "id": f"sd-ranked-{tier}-{i:02d}", "difficulty_rating": rating}
            dbg = {**copy.deepcopy(TAP), "id": f"dbg-ranked-{tier}-{i:02d}", "difficulty_rating": rating}
            sd.pop("placement", None)
            dbg.pop("placement", None)
            questions += [sd, dbg]
            ids += [sd["id"], dbg["id"]]
        tiers.append({"id": tier, "title": tier.title(), "description": "x", "time_limit_s": 600,
                      "min_rating": lo, "max_rating": hi, "questions": ids})
    return questions, {"version": 1, "tiers": tiers}


MODULE = {
    "topic": "caching", "version": 1, "track": "system-design", "title": "Caching", "summary": "Why caches work.",
    "minutes": 5,
    "sections": [
        {"id": f"s{i}", "heading": f"Part {i}", "body": ["Text."], "example": {"title": "Ex", "text": "Walkthrough."},
         "check": {"prompt": "Pick b", "options": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}, {"id": "c", "text": "C"}],
                   "answer": "b", "explanation": "Because b."}}
        for i in range(1, 4)
    ],
    "sources": [{"title": "Redis docs", "url": "https://redis.io/docs/", "publisher": "Redis"},
                {"title": "MDN HTTP caching", "url": "https://developer.mozilla.org/", "publisher": "Mozilla"}],
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DEMO_MODE", "1")
    content = tmp_path / "content"
    (content / "system-design").mkdir(parents=True)
    (content / "debugging").mkdir()
    (content / "ranked").mkdir()
    (content / "learn").mkdir()
    (content / "system-design" / "q.json").write_text(json.dumps([q for q in ROOT_EXAMPLES if q["track"] == "system-design"]))
    (content / "debugging" / "q.json").write_text(json.dumps([TAP]))
    rq, manifest = ranked_content()
    (content / "ranked" / "questions.json").write_text(json.dumps(rq))
    (content / "ranked" / "tests.json").write_text(json.dumps(manifest))
    (content / "learn" / "caching.json").write_text(json.dumps(MODULE))
    from api import content_loader

    monkeypatch.setattr(content_loader, "CONTENT", content)
    from api.main import app

    with TestClient(app) as c:
        yield c


def guest(client):
    uid = client.post("/v1/users", json={"display_name": "Guest"}).json()["user_id"]
    return uid, {"X-User-Id": uid}


def account(client, name="alice"):
    uid, h = guest(client)
    r = client.post("/v1/auth/signup", headers=h, json={"username": name, "password": "correct horse"})
    assert r.status_code == 201, r.text
    return r.json(), {"Authorization": f"Bearer {r.json()['token']}"}


# ---- accounts ----------------------------------------------------------------

def test_signup_claims_guest_progress_and_locks_the_id(client):
    uid, h = guest(client)
    r = client.post("/v1/auth/signup", headers=h, json={"username": "Alice_1", "password": "correct horse"})
    assert r.status_code == 201
    body = r.json()
    assert body["claimed_guest"] is True and body["user"]["user_id"] == uid and body["user"]["username"] == "alice_1"
    # The id alone no longer works once a password exists.
    assert client.get("/v1/me", headers=h).json()["error"]["code"] == "session_expired"
    me = client.get("/v1/me", headers={"Authorization": f"Bearer {body['token']}"}).json()
    assert me["has_account"] is True and me["user_id"] == uid


def test_login_logout_and_bad_password(client):
    account(client, "bob")
    assert client.post("/v1/auth/login", json={"username": "bob", "password": "nope nope"}).status_code == 401
    r = client.post("/v1/auth/login", json={"username": "BOB", "password": "correct horse"})
    assert r.status_code == 200
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    assert client.get("/v1/me", headers=h).status_code == 200
    client.post("/v1/auth/logout", headers=h)
    assert client.get("/v1/me", headers=h).status_code == 401


def test_signup_rules(client):
    account(client, "carol")
    assert client.post("/v1/auth/signup", json={"username": "carol", "password": "correct horse"}).json()["error"]["code"] == "username_taken"
    assert client.post("/v1/auth/signup", json={"username": "x", "password": "correct horse"}).status_code == 422
    assert client.post("/v1/auth/signup", json={"username": "dave", "password": "short"}).status_code == 422
    assert client.post("/v1/auth/signup", json={"username": "sample_user_99", "password": "correct horse"}).status_code == 422


def test_login_rate_limit(client):
    account(client, "erin")
    for _ in range(10):
        client.post("/v1/auth/login", json={"username": "erin", "password": "wrong pass"})
    r = client.post("/v1/auth/login", json={"username": "erin", "password": "correct horse"})
    assert r.status_code == 429


def test_demo_user_signup_does_not_claim_demo(client):
    r = client.post("/v1/auth/signup", headers={"X-User-Id": "demo"}, json={"username": "frank", "password": "correct horse"})
    assert r.json()["claimed_guest"] is False and r.json()["user"]["user_id"] != "demo"


# ---- learning modules ----------------------------------------------------------

def test_learn_gating_and_completion(client):
    _, h = guest(client)
    mods = client.get("/v1/learn", headers=h).json()["modules"]
    assert [m["topic"] for m in mods] == ["caching"] and mods[0]["completed"] is False
    m = client.get("/v1/learn/caching", headers=h).json()
    assert "answer" not in m["sections"][0]["check"] and "explanation" not in m["sections"][0]["check"]
    assert len(m["sources"]) == 2

    assert client.post("/v1/learn/caching/check", headers=h, json={"section_id": "s2", "response": "b"}).json()["error"]["code"] == "locked"
    wrong = client.post("/v1/learn/caching/check", headers=h, json={"section_id": "s1", "response": "a"}).json()
    assert wrong["correct"] is False and "explanation" not in wrong
    for s in ("s1", "s2", "s3"):
        r = client.post("/v1/learn/caching/check", headers=h, json={"section_id": s, "response": "b"}).json()
        assert r["correct"] and r["explanation"]
    assert r["completed"] is True
    assert client.get("/v1/learn", headers=h).json()["modules"][0]["completed"] is True


def test_learn_does_not_touch_elo(client):
    _, h = guest(client)
    before = client.get("/v1/progress", headers=h).json()
    client.post("/v1/learn/caching/check", headers=h, json={"section_id": "s1", "response": "b"})
    assert client.get("/v1/progress", headers=h).json()["topics"] == before["topics"]


# ---- ranked tests ----------------------------------------------------------------

def test_ranked_questions_never_in_lessons_or_placement(client):
    from api import db, repo

    with db.transaction() as conn:
        ids = {c.id for c in repo.candidates(conn)}
    assert ids and not any("-ranked-" in i for i in ids)


def test_guest_cannot_start(client):
    _, h = guest(client)
    listing = client.get("/v1/ranked", headers=h).json()
    assert listing["has_account"] is False and len(listing["tiers"]) == 3
    assert client.post("/v1/ranked/beginner/start", headers=h).json()["error"]["code"] == "account_required"


def test_full_attempt_once_only(client):
    _, h = account(client)
    s = client.post("/v1/ranked/beginner/start", headers=h).json()
    assert len(s["questions"]) == 10 and s["remaining_ms"] > 590_000
    assert all("answer" not in q for q in s["questions"])
    # Answer everything correctly except the last; no feedback while running.
    for q in s["questions"][:-1]:
        ans = MCQ["answer"] if q["format"] == "mcq" else TAP["answer"]
        r = client.post("/v1/ranked/beginner/answer", headers=h, json={"question_id": q["id"], "response": ans}).json()
        assert "correct" not in r and r["saved"]
    q0 = s["questions"][0]["id"]
    assert client.post("/v1/ranked/beginner/answer", headers=h, json={"question_id": q0, "response": "a"}).json()["error"]["code"] == "already_answered"
    # Resume returns saved answers.
    assert len(client.get("/v1/ranked/beginner/attempt", headers=h).json()["answered"]) == 9

    res = client.post("/v1/ranked/beginner/submit", headers=h).json()
    assert res["status"] == "finished" and res["score"] == 9 and res["total"] == 10
    assert len(res["review"]) == 10 and res["review"][-1]["response"] is None and res["review"][-1]["correct"] is False
    assert res["rank"] >= 1 and res["takers"] == 26  # 24 samples + demo user + me
    # Never again.
    assert client.post("/v1/ranked/beginner/start", headers=h).json()["error"]["code"] == "already_taken"


def test_timeout_finalizes_and_scores_unanswered_wrong(client, monkeypatch):
    _, h = account(client)
    s = client.post("/v1/ranked/intermediate/start", headers=h).json()
    q = s["questions"][0]
    client.post("/v1/ranked/intermediate/answer", headers=h, json={"question_id": q["id"], "response": MCQ["answer"]})
    real = clock.now()
    monkeypatch.setattr(clock, "now", lambda: real + 601)
    late = client.post("/v1/ranked/intermediate/answer", headers=h, json={"question_id": s["questions"][1]["id"], "response": TAP["answer"]})
    assert late.json()["error"]["code"] == "time_up"
    res = client.get("/v1/ranked/intermediate/result", headers=h).json()
    assert res["score"] == 1 and res["time_ms"] == 600_000


def test_ranked_updates_student_elo_not_question(client):
    from api import db

    _, h = account(client)
    s = client.post("/v1/ranked/advanced/start", headers=h).json()
    q = s["questions"][0]
    with db.transaction() as conn:
        qr = conn.execute("SELECT live_rating FROM questions WHERE id = ?", (q["id"],)).fetchone()[0]
    client.post("/v1/ranked/advanced/answer", headers=h, json={"question_id": q["id"], "response": MCQ["answer"]})
    with db.transaction() as conn:
        assert conn.execute("SELECT live_rating FROM questions WHERE id = ?", (q["id"],)).fetchone()[0] == qr
    caching = next(t for t in client.get("/v1/progress", headers=h).json()["topics"] if t["topic"] == q["topic"])
    assert caching["rating"] > 1200


def test_leaderboard_has_labeled_samples_and_you(client):
    _, h = account(client)
    s = client.post("/v1/ranked/beginner/start", headers=h).json()
    client.post("/v1/ranked/beginner/submit", headers=h)
    board = client.get("/v1/ranked/beginner/leaderboard", headers=h).json()
    assert board["takers"] == 26
    assert any(e["sample"] and e["username"].startswith("sample_user_") for e in board["top"])
    assert board["you"]["score"] == 0 and board["you"]["rank"] == 26 and board["you"]["top_percent"] == 100
    ranks = [(-e["score"], e["time_ms"]) for e in board["top"]]
    assert ranks == sorted(ranks)


def test_demo_user_has_seeded_beginner_attempt(client):
    h = {"X-User-Id": "demo"}
    tiers = {t["id"]: t for t in client.get("/v1/ranked", headers=h).json()["tiers"]}
    assert tiers["beginner"]["attempt"]["status"] == "finished" and tiers["beginner"]["attempt"]["score"] == 8
    assert tiers["advanced"]["attempt"] is None


def test_feature_flag_hides_routes(client, monkeypatch):
    monkeypatch.setenv("FEATURE_RANKED", "0")
    _, h = guest(client)
    assert client.get("/v1/ranked", headers=h).status_code == 404
    assert client.get("/v1/config").json()["features"]["ranked"] is False
