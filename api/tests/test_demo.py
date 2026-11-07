import pytest

D = {"X-Client-Date": "2026-11-08"}


@pytest.fixture()
def demo_client(client, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    return client


def test_demo_routes_hidden_without_demo_mode(client):
    assert client.post("/v1/demo/switch", json={"user_id": "demo"}).status_code == 404
    assert client.post("/v1/demo/reset", json={"user_id": "demo"}).status_code == 404


def test_demo_user_exists_after_boot(client):
    assert client.get("/v1/me", headers={"X-User-Id": "demo"}).json()["placed"] is True


def test_switch_gives_day_seven_story(demo_client):
    r = demo_client.post("/v1/demo/switch", headers=D, json={"user_id": "demo"}).json()
    assert r["user_id"] == "demo" and r["placed"] is True
    assert r["streak"] == {"current": 6, "best": 6, "today_done": False}

    h = {**D, "X-User-Id": "demo"}
    lesson = demo_client.get("/v1/lessons/today", headers=h).json()
    assert 1 <= len(lesson["items"]) <= 3
    done = demo_client.post(f"/v1/lessons/{lesson['lesson_id']}/complete", headers=h).json()
    assert done["streak"]["current"] == 7 and done["streak"]["extended"] is True

    # A second run of the demo starts clean again.
    again = demo_client.post("/v1/demo/switch", headers=D, json={"user_id": "demo"}).json()
    assert again["streak"]["current"] == 6 and again["streak"]["today_done"] is False


def test_reset_is_fast_and_clears_lessons(demo_client):
    import time

    h = {**D, "X-User-Id": "demo"}
    demo_client.get("/v1/lessons/today", headers=h)
    t = time.perf_counter()
    assert demo_client.post("/v1/demo/reset", headers=D, json={"user_id": "demo"}).json() == {"ok": True}
    assert time.perf_counter() - t < 1.0
    assert demo_client.get("/v1/progress", headers=h).json()["streak"]["current"] == 6


def test_advance_day(demo_client):
    h = {**D, "X-User-Id": "demo"}
    assert demo_client.post("/v1/demo/advance-day", headers=h).json() == {"date": "2026-11-09"}
    assert demo_client.get("/v1/lessons/today", headers=h).json()["date"] == "2026-11-09"
    assert demo_client.post("/v1/demo/advance-day", headers=D).status_code == 401
