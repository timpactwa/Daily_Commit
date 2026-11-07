"""Daily streak rules (contracts/api.md, lesson complete)."""
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class Streak:
    current: int
    best: int
    last: str | None  # YYYY-MM-DD of the last completed lesson


def _yesterday(day: str) -> str:
    return (date.fromisoformat(day) - timedelta(days=1)).isoformat()


def complete(s: Streak, today: str) -> tuple[Streak, bool]:
    """Apply a completed lesson on `today`. Returns (new streak, extended?)."""
    if s.last == today:
        return s, False
    current = s.current + 1 if s.last == _yesterday(today) else 1
    return Streak(current, max(s.best, current), today), True


def visible(s: Streak, today: str) -> int:
    """Streak shown to the user: alive only if the last lesson was today or yesterday."""
    return s.current if s.last in (today, _yesterday(today)) else 0
