from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert isinstance(r.json()["questions"], int)


def test_unknown_route_404():
    assert client.get("/v1/does-not-exist").status_code == 404
