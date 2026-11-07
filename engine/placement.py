"""Placement test: which questions to ask, and how answers spill over. See contracts/rating.md."""
import random

from engine.elo import SPILLOVER, clamp
from engine.selection import Candidate

TARGETS = {"easy": 1000.0, "medium": 1200.0, "hard": 1400.0}
# Per track of 5 topics. Two tracks give 2 easy / 4 medium / 4 hard in total.
TRACK_MIX = ["easy", "medium", "medium", "hard", "hard"]


def choose(
    pool: list[Candidate],
    topic_track: dict[str, str],
    seed: str,
    limit: int | None = None,
) -> list[Candidate]:
    """One question per topic with the difficulty mix, ordered easy to hard, tracks interleaved.

    Prefers questions flagged for placement (pass those first in `pool` or only those);
    falls back to any question in the topic. Topics with no questions are skipped.
    `limit` (demo) keeps that many topics, split evenly across tracks.
    """
    rng = random.Random(seed)
    by_topic: dict[str, list[Candidate]] = {}
    for c in pool:
        by_topic.setdefault(c.topic, []).append(c)

    per_track: dict[str, list[tuple[str, str]]] = {}
    for track in sorted(set(topic_track.values())):
        topics = sorted(t for t, tr in topic_track.items() if tr == track)
        mix = (TRACK_MIX * ((len(topics) // len(TRACK_MIX)) + 1))[: len(topics)]
        rng.shuffle(topics)
        per_track[track] = [(t, band) for t, band in zip(topics, mix) if by_topic.get(t)]

    if limit is not None:
        tracks = list(per_track)
        keep = {tr: limit // len(tracks) + (1 if i < limit % len(tracks) else 0) for i, tr in enumerate(tracks)}
        for tr in tracks:
            # keep a spread of bands: take every k-th entry sorted by band
            entries = sorted(per_track[tr], key=lambda e: TARGETS[e[1]])
            n = min(keep[tr], len(entries))
            step = len(entries) / n if n else 1
            per_track[tr] = [entries[int(i * step)] for i in range(n)]

    chosen: list[tuple[float, int, Candidate]] = []
    for track_index, entries in enumerate(per_track.values()):
        for topic, band in entries:
            target = TARGETS[band]
            best = min(by_topic[topic], key=lambda c: (abs(c.rating - target), c.id))
            chosen.append((target, track_index, best))
    chosen.sort(key=lambda x: (x[0], x[1]))
    return [c for _, _, c in chosen]


def spillover(
    ratings: dict[str, float], answered_topic: str, delta: float, topic_track: dict[str, str]
) -> dict[str, float]:
    """New ratings for the other topics in the answered topic's track."""
    track = topic_track[answered_topic]
    return {
        t: clamp(ratings[t] + SPILLOVER * delta)
        for t, tr in topic_track.items()
        if tr == track and t != answered_topic and t in ratings
    }
