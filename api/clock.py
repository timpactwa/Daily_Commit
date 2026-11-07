"""Server clock in epoch seconds. Tests monkeypatch `now` to move time."""
import time


def now() -> float:
    return time.time()
