from api import db


def new_user(client):
    uid = client.post("/v1/users", json={"display_name": "P"}).json()["user_id"]
    return {"X-User-Id": uid, "X-Client-Date": "2026-11-08"}


def correct_response(q):
    with db.transaction() as conn:
        import json
        full = json.loads(conn.execute("SELECT data FROM questions WHERE id = ?", (q["id"],)).fetchone()["data"])
    return full["answer"]


def test_placement_flow_places_user_and_spills_over(client):
    h = new_user(client)
    qs = client.get("/v1/placement", headers=h).json()["questions"]
    assert qs and all("answer" not in q for q in qs)
    assert len({q["topic"] for q in qs}) == len(qs)

    caching = next(q for q in qs if q["topic"] == "caching")
    r = client.post("/v1/placement", headers=h, json={"responses": [
        {"question_id": caching["id"], "response": correct_response(caching), "time_ms": 4000}
    ]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["results"] == [{"question_id": caching["id"], "correct": True}]
    by_topic = {t["topic"]: t for t in body["topics"]}
    assert len(by_topic) == 10
    assert by_topic["caching"]["rating"] > by_topic["scaling"]["rating"] > 1200  # spillover, same track
    assert by_topic["recursion"]["rating"] == 1200  # other track untouched

    assert client.get("/v1/me", headers=h).json()["placed"] is True
    assert client.get("/v1/lessons/today", headers=h).status_code == 200


def test_placement_rejects_duplicates_and_unknown(client):
    h = new_user(client)
    dup = {"question_id": "sd-caching-001", "response": "b"}
    assert client.post("/v1/placement", headers=h, json={"responses": [dup, dup]}).status_code == 422
    r = client.post("/v1/placement", headers=h, json={"responses": [{"question_id": "nope", "response": "b"}]})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_response"
    assert client.get("/v1/me", headers=h).json()["placed"] is False  # rolled back


def test_limit_only_in_demo_mode(client, monkeypatch):
    h = new_user(client)
    full = len(client.get("/v1/placement?limit=2", headers=h).json()["questions"])
    monkeypatch.setenv("DEMO_MODE", "1")
    assert len(client.get("/v1/placement?limit=2", headers=h).json()["questions"]) == 2
    assert full >= 2
