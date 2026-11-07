from collections import Counter

from engine import placement
from engine.selection import Candidate

TOPIC_TRACK = {
    **{t: "system-design" for t in ["caching", "scaling", "databases", "async-messaging", "reliability"]},
    **{t: "debugging" for t in ["arrays-strings", "binary-search", "recursion", "sorting", "hash-maps"]},
}


def full_pool():
    return [
        Candidate(f"{t}-{band}", t, tr, rating)
        for t, tr in TOPIC_TRACK.items()
        for band, rating in placement.TARGETS.items()
    ]


def test_ten_questions_one_per_topic_with_mix():
    qs = placement.choose(full_pool(), TOPIC_TRACK, seed="u1")
    assert len(qs) == 10
    assert len({q.topic for q in qs}) == 10
    bands = Counter(q.id.rsplit("-", 1)[1] for q in qs)
    assert bands == {"easy": 2, "medium": 4, "hard": 4}
    for track in ("system-design", "debugging"):
        assert {q.id.rsplit("-", 1)[1] for q in qs if q.track == track} == {"easy", "medium", "hard"}


def test_ordered_easy_to_hard():
    ratings = [q.rating for q in placement.choose(full_pool(), TOPIC_TRACK, seed="u2")]
    assert ratings == sorted(ratings)


def test_seed_changes_assignment_but_is_stable():
    a = placement.choose(full_pool(), TOPIC_TRACK, seed="u1")
    assert a == placement.choose(full_pool(), TOPIC_TRACK, seed="u1")
    assert any(placement.choose(full_pool(), TOPIC_TRACK, seed=s) != a for s in ("x", "y", "z"))


def test_limit_splits_tracks():
    qs = placement.choose(full_pool(), TOPIC_TRACK, seed="demo", limit=4)
    assert len(qs) == 4
    assert Counter(q.track for q in qs) == {"system-design": 2, "debugging": 2}


def test_skips_topics_without_questions():
    pool = [c for c in full_pool() if c.topic in ("caching", "recursion")]
    qs = placement.choose(pool, TOPIC_TRACK, seed="u1")
    assert {q.topic for q in qs} == {"caching", "recursion"}


def test_spillover_vector():
    ratings = {t: 1200.0 for t in TOPIC_TRACK}
    out = placement.spillover(ratings, "caching", 182.34, TOPIC_TRACK)
    assert set(out) == {"scaling", "databases", "async-messaging", "reliability"}
    assert all(round(v, 2) == 1254.70 for v in out.values())
