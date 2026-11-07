"""Lesson selection. Pure: callers pass ratings, candidates and history. Spec: contracts/rating.md.

Slots for a 6-item lesson:
  2 focus  from the weakest topic        (weakness W = R - 100 * misses in the latest lesson)
  1 focus  from the second weakest topic
  2 mix    other topics, guaranteeing both tracks appear
  1 review most recent earlier miss (else another focus item)
Each slot targets Q* = R - 150 (~70% expected success) and picks randomly among the 3 closest,
seeded by (user, date) so a lesson is stable for the day. If a topic has nothing within
DIFFICULTY_TOLERANCE of its target (easy questions used up), the slot moves to the next topic
in line before falling back to the closest question anywhere; simulation (engine/simulate.py)
showed this lifts real success from ~49% to ~60% and stops it sliding over the weeks. A debugging source function appears at
most once per lesson and not if shown in the last 3 days.
"""
import random
from dataclasses import dataclass, field

from engine.elo import expected, target_difficulty

LESSON_SIZE = 6
MISS_PRESSURE = 100.0
BEST_OF = 3
DIFFICULTY_TOLERANCE = 150.0


@dataclass(frozen=True)
class Candidate:
    id: str
    topic: str
    track: str
    rating: float
    source_function: str | None = None


@dataclass
class History:
    misses_in_latest_lesson: dict[str, int] = field(default_factory=dict)  # topic -> misses
    recently_answered: set[str] = field(default_factory=set)               # question ids, last 3 days
    recent_functions: set[str] = field(default_factory=set)                # source functions, last 3 days
    review_ids: list[str] = field(default_factory=list)                    # earlier misses, newest first


@dataclass(frozen=True)
class Pick:
    question_id: str
    topic: str
    track: str
    rating: float
    kind: str  # focus | mix | review


def weakness(ratings: dict[str, float], history: History) -> dict[str, float]:
    return {t: r - MISS_PRESSURE * history.misses_in_latest_lesson.get(t, 0) for t, r in ratings.items()}


def build_lesson(
    ratings: dict[str, float],
    pool: list[Candidate],
    history: History | None = None,
    seed: str = "",
    size: int = LESSON_SIZE,
) -> list[Pick]:
    history = history or History()
    rng = random.Random(seed)
    by_id = {c.id: c for c in pool}
    topic_track = {c.topic: c.track for c in pool}
    W = weakness({t: ratings.get(t, 1200.0) for t in topic_track}, history)
    order = sorted(topic_track, key=lambda t: (W[t], t))  # weakest first

    picks: list[Pick] = []
    used_ids: set[str] = set()
    used_functions: set[str] = set()

    def available(topic: str) -> list[Candidate]:
        return [
            c for c in pool
            if c.topic == topic
            and c.id not in used_ids
            and c.id not in history.recently_answered
            and not (c.source_function and (c.source_function in used_functions or c.source_function in history.recent_functions))
        ]

    def take(c: Candidate, kind: str) -> None:
        used_ids.add(c.id)
        if c.source_function:
            used_functions.add(c.source_function)
        picks.append(Pick(c.id, c.topic, c.track, c.rating, kind))

    def fill(topic: str, kind: str, tolerance: float | None = None) -> bool:
        options = available(topic)
        if not options:
            return False
        target = target_difficulty(ratings.get(topic, 1200.0))
        options.sort(key=lambda c: (abs(c.rating - target), c.id))
        if history.misses_in_latest_lesson.get(topic) and all(p.topic != topic for p in picks):
            tolerance = None  # just missed: guarantee one more try even if nothing fits perfectly
        near = [c for c in options[:BEST_OF] if tolerance is None or abs(c.rating - target) <= tolerance]
        if not near:
            return False
        take(rng.choice(near), kind)
        return True

    def fill_first(topics: list[str], kind: str) -> str | None:
        # First pass: only questions near the target. Second pass: closest available.
        for tolerance in (DIFFICULTY_TOLERANCE, None):
            for t in topics:
                if fill(t, kind, tolerance):
                    return t
        return None

    if size < LESSON_SIZE:
        # Short demo lesson: weakest topic of each track, then one mix item.
        for track in sorted(set(topic_track.values()), key=lambda tr: min(W[t] for t in order if topic_track[t] == tr)):
            fill_first([t for t in order if topic_track[t] == track], "focus")
        rest = [t for t in order if t not in {p.topic for p in picks}]
        rng.shuffle(rest)
        while len(picks) < size and fill_first(rest, "mix"):
            pass
    else:
        weakest = fill_first(order, "focus")
        if weakest:
            fill(weakest, "focus", DIFFICULTY_TOLERANCE)
        second = fill_first([t for t in order if t != weakest], "focus")
        focus = {weakest, second} - {None}

        # Mix: first from a track the focus items don't cover yet, then any other topic.
        covered = {p.track for p in picks}
        others = [t for t in order if t not in focus]
        rng.shuffle(others)
        missing = [t for t in others if topic_track[t] not in covered]
        first_mix = fill_first(missing or others, "mix")
        fill_first([t for t in others if t != first_mix], "mix")

        review = next((by_id[q] for q in history.review_ids if q in by_id and q not in used_ids), None)
        if review:
            take(review, "review")

        # Top up (missing review, or topics that ran out of questions) with focus items.
        while len(picks) < size and fill_first(order, "focus"):
            pass
    return order_items(picks[:size], ratings)


def order_items(picks: list[Pick], ratings: dict[str, float]) -> list[Pick]:
    """Start with the likeliest win, end on a mix item, alternate tracks in between."""
    if len(picks) < 3:
        return picks
    p_win = {p.question_id: expected(ratings.get(p.topic, 1200.0), p.rating) for p in picks}
    mixes = [p for p in picks if p.kind == "mix"]
    last = max(mixes, key=lambda p: p_win[p.question_id]) if mixes else None
    rest = [p for p in picks if p is not last]
    first = max(rest, key=lambda p: p_win[p.question_id])
    middle = [p for p in rest if p is not first]
    ordered = [first]
    while middle:
        prev = ordered[-1].track
        nxt = next((p for p in middle if p.track != prev), middle[0])
        ordered.append(nxt)
        middle.remove(nxt)
    return ordered + ([last] if last else [])
