"""Lesson selection. Pure: callers pass in ratings, candidates and history.

T2 ships a naive version (weakest topics first, closest difficulty). C2 replaces
`build_lesson` with the full algorithm in contracts/rating.md; the signature stays.
"""
from dataclasses import dataclass, field

from engine.elo import target_difficulty

LESSON_SIZE = 6


@dataclass(frozen=True)
class Candidate:
    id: str
    topic: str
    track: str
    rating: float
    source_function: str | None = None


@dataclass
class History:
    """What the user has recently done; all optional for the naive version."""
    misses_in_latest_lesson: dict[str, int] = field(default_factory=dict)  # topic -> misses
    recently_answered: set[str] = field(default_factory=set)               # question ids, last 3 days
    recent_functions: set[str] = field(default_factory=set)                # source functions, last 3 days


@dataclass(frozen=True)
class Pick:
    question_id: str
    topic: str
    kind: str  # focus | mix | review


def build_lesson(
    ratings: dict[str, float],
    pool: list[Candidate],
    history: History | None = None,
    seed: str = "",
    size: int = LESSON_SIZE,
) -> list[Pick]:
    history = history or History()
    by_topic: dict[str, list[Candidate]] = {}
    for c in pool:
        if c.id not in history.recently_answered:
            by_topic.setdefault(c.topic, []).append(c)
    topics = sorted((t for t in by_topic), key=lambda t: ratings.get(t, 1200.0))

    picks: list[Pick] = []
    used: set[str] = set()
    while len(picks) < size and any(by_topic.values()):
        for i, topic in enumerate(topics):
            if len(picks) >= size:
                break
            options = [c for c in by_topic[topic] if c.id not in used]
            if not options:
                continue
            target = target_difficulty(ratings.get(topic, 1200.0))
            best = min(options, key=lambda c: (abs(c.rating - target), c.id))
            used.add(best.id)
            picks.append(Pick(best.id, topic, "focus" if i < 2 else "mix"))
        if not any(c.id not in used for cs in by_topic.values() for c in cs):
            break
    return picks
