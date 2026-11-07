import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Fresh SQLite file per test; lifespan runs (schema + content load)."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    # Pin content to contracts/examples (empty dir -> fallback) so tests don't depend on /content.
    from api import content_loader

    empty = tmp_path / "no-content"
    empty.mkdir()
    monkeypatch.setattr(content_loader, "CONTENT", empty)
    from api.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def placed_user(client):
    """A user marked as placed (placement endpoint arrives in C1)."""
    from api import db

    uid = client.post("/v1/users", json={"display_name": "Test"}).json()["user_id"]
    with db.transaction() as conn:
        conn.execute("UPDATE users SET placed = 1 WHERE id = ?", (uid,))
    return {"X-User-Id": uid, "X-Client-Date": "2026-11-08"}
