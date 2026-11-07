from api import db


def test_health_counts_loaded_questions(client):
    assert client.get("/health").json()["questions"] >= 4  # falls back to contracts/examples


def test_topics(client):
    assert len(client.get("/v1/topics").json()["topics"]) == 10


def test_create_user_and_me(client):
    r = client.post("/v1/users", json={"display_name": "Liam"})
    assert r.status_code == 201
    body = r.json()
    assert body["user_id"].startswith("u_") and body["placed"] is False
    me = client.get("/v1/me", headers={"X-User-Id": body["user_id"]}).json()
    assert me["streak"] == {"current": 0, "best": 0, "today_done": False}


def test_unknown_user(client):
    r = client.get("/v1/me", headers={"X-User-Id": "nope"})
    assert r.status_code == 401
    assert r.json() == {"error": {"code": "unknown_user", "message": "Missing or unknown X-User-Id"}}


def test_lesson_requires_placement(client):
    uid = client.post("/v1/users", json={}).json()["user_id"]
    r = client.get("/v1/lessons/today", headers={"X-User-Id": uid})
    assert r.status_code == 409 and r.json()["error"]["code"] == "not_placed"


def test_lesson_is_idempotent_and_hides_answers(client, placed_user):
    a = client.get("/v1/lessons/today", headers=placed_user).json()
    b = client.get("/v1/lessons/today", headers=placed_user).json()
    assert a == b
    assert a["date"] == "2026-11-08" and a["status"] == "in_progress"
    assert len(a["items"]) >= 4
    for item in a["items"]:
        q = item["question"]
        assert not {"answer", "explanation", "provenance"} & q.keys()
        if q["format"] == "reorder":
            assert [o["id"] for o in q["options"]] != sorted(o["id"] for o in q["options"])


def test_answer_updates_ratings_and_persists(client, placed_user):
    lesson = client.get("/v1/lessons/today", headers=placed_user).json()
    item = next(i for i in lesson["items"] if i["question"]["format"] == "tap_line")
    q = item["question"]
    r = client.post("/v1/answers", headers=placed_user,
                    json={"lesson_id": lesson["lesson_id"], "question_id": q["id"], "response": 3, "time_ms": 900})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["correct"] is True and body["score"] == 1.0 and body["correct_answer"] == 3
    assert body["rating"]["delta"] > 0 and body["question_rating"]["after"] < body["question_rating"]["before"]
    assert body["provenance"]["mutation_operator"] == "flip_comparison"
    assert body["lesson_progress"]["answered"] == 1

    with db.transaction() as conn:
        rating = conn.execute("SELECT rating, answers FROM user_topics WHERE user_id = ? AND topic = ?",
                              (placed_user["X-User-Id"], q["topic"])).fetchone()
    assert round(rating["rating"]) == body["rating"]["after"] and rating["answers"] == 1

    again = client.get("/v1/lessons/today", headers=placed_user).json()
    done = next(i for i in again["items"] if i["question"]["id"] == q["id"])
    assert done["answered"] is True and done["correct"] is True


def test_duplicate_and_bad_answers(client, placed_user):
    lesson = client.get("/v1/lessons/today", headers=placed_user).json()
    mcq = next(i["question"] for i in lesson["items"] if i["question"]["format"] == "mcq")
    base = {"lesson_id": lesson["lesson_id"], "question_id": mcq["id"]}
    assert client.post("/v1/answers", headers=placed_user, json={**base, "response": 2}).json()["error"]["code"] == "invalid_response"
    assert client.post("/v1/answers", headers=placed_user, json={**base, "response": "a"}).json()["correct"] is False
    r = client.post("/v1/answers", headers=placed_user, json={**base, "response": "b"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "already_answered"
    r = client.post("/v1/answers", headers=placed_user, json={**base, "lesson_id": "l_nope"})
    assert r.status_code == 404 or r.status_code == 422


def test_reload_keeps_learned_rating(client, placed_user):
    from api import content_loader

    lesson = client.get("/v1/lessons/today", headers=placed_user).json()
    q = lesson["items"][0]["question"]
    client.post("/v1/answers", headers=placed_user,
                json={"lesson_id": lesson["lesson_id"], "question_id": q["id"], "response": "zzz" if q["format"] != "tap_line" and q["format"] != "reorder" else (99 if q["format"] == "tap_line" else [o["id"] for o in q["options"]])})
    with db.transaction() as conn:
        before = conn.execute("SELECT live_rating, seed_rating FROM questions WHERE id = ?", (q["id"],)).fetchone()
        content_loader.load(conn)
        after = conn.execute("SELECT live_rating FROM questions WHERE id = ?", (q["id"],)).fetchone()
    assert before["live_rating"] != before["seed_rating"]
    assert after["live_rating"] == before["live_rating"]
