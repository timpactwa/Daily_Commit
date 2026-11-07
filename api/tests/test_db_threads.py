"""A request's connection can be opened in one thread and used/closed in another."""
import threading

from api import db


def test_connection_usable_across_threads(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    db.init()
    conn = db.connect()
    errors = []

    def use():
        try:
            conn.execute("SELECT COUNT(*) FROM users").fetchone()
            conn.commit()
            conn.close()
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    t = threading.Thread(target=use)
    t.start()
    t.join()
    assert errors == []
