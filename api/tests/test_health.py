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


def test_spa_fallback_serves_index_for_deep_links(tmp_path, monkeypatch):
    import asyncio

    from api.main import SpaFiles

    (tmp_path / "index.html").write_text("<html>app</html>")
    files = SpaFiles(directory=tmp_path, html=True)
    scope = {"type": "http", "method": "GET", "headers": []}
    r = asyncio.run(files.get_response("ranked/beginner/play", scope))
    assert r.status_code == 200
    import pytest
    from starlette.exceptions import HTTPException

    with pytest.raises(HTTPException):
        asyncio.run(files.get_response("assets/missing.js", scope))
    with pytest.raises(HTTPException):
        asyncio.run(files.get_response("v1/nothing", scope))
