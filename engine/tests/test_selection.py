from collections import Counter

from engine.selection import Candidate, History, build_lesson

SD = ["caching", "scaling", "databases", "async-messaging", "reliability"]
DBG = ["arrays-strings", "binary-search", "recursion", "sorting", "hash-maps"]
TRACK = {**{t: "system-design" for t in SD}, **{t: "debugging" for t in DBG}}


def pool():
    out = []
    for t, tr in TRACK.items():
        for i, r in enumerate(range(900, 1600, 70)):  # 10 per topic
            fn = f"{t}_fn{i // 3}" if tr == "debugging" else None  # 3 mutants per function
            out.append(Candidate(f"{t}-{i}", t, tr, float(r), fn))
    return out


def ratings(**over):
    r = {t: 1250.0 for t in TRACK}
    r.update({k.replace("_", "-"): v for k, v in over.items()})
    return r


def test_six_items_weakest_topic_gets_two_focus():
    picks = build_lesson(ratings(databases=1000, recursion=1100), pool(), seed="u:2026-11-08")
    assert len(picks) == 6
    focus = Counter(p.topic for p in picks if p.kind == "focus")
    assert focus["databases"] >= 2
    assert focus["recursion"] >= 1


def test_both_tracks_present():
    picks = build_lesson(ratings(caching=900, scaling=950), pool(), seed="s")
    assert {p.track for p in picks} == {"system-design", "debugging"}


def test_one_miss_moves_topic_into_focus():
    base = ratings(databases=1150, sorting=1180)
    before = build_lesson(base, pool(), seed="s")
    assert "hash-maps" not in {p.topic for p in before if p.kind == "focus"}
    after = build_lesson(base, pool(), History(misses_in_latest_lesson={"hash-maps": 1}), seed="s")
    assert "hash-maps" in {p.topic for p in after if p.kind == "focus"}


def test_difficulty_near_target():
    picks = build_lesson(ratings(databases=1000), pool(), seed="s")
    for p in picks:
        if p.topic == "databases":
            assert abs(p.rating - 850) <= 3 * 70 + 50  # among the closest to R - 150


def test_stable_for_same_seed_and_varies_otherwise():
    r = ratings(databases=1000)
    assert build_lesson(r, pool(), seed="u:d1") == build_lesson(r, pool(), seed="u:d1")
    assert any(build_lesson(r, pool(), seed=f"u:d{i}") != build_lesson(r, pool(), seed="u:d1") for i in range(2, 8))


def test_no_repeated_source_function():
    for s in range(20):
        picks = build_lesson(ratings(recursion=900), pool(), seed=str(s))
        fns = [p.question_id for p in picks if p.track == "debugging"]
        by_fn = Counter(next(c.source_function for c in pool() if c.id == q) for q in fns)
        assert max(by_fn.values(), default=1) == 1


def test_recent_functions_and_answers_excluded():
    recent_fns = {f"recursion_fn{i}" for i in range(3)}
    answered = {"databases-0", "databases-1", "databases-2"}
    picks = build_lesson(ratings(recursion=900, databases=950), pool(),
                         History(recently_answered=answered, recent_functions=recent_fns), seed="s")
    assert not answered & {p.question_id for p in picks}
    rec = [p for p in picks if p.topic == "recursion"]
    assert all(p.question_id.endswith("-9") for p in rec)  # only fn3 left


def test_review_slot_uses_earlier_miss():
    picks = build_lesson(ratings(), pool(), History(review_ids=["sorting-4"]), seed="s")
    assert [p.question_id for p in picks if p.kind == "review"] == ["sorting-4"]


def test_order_starts_easy_ends_on_mix():
    picks = build_lesson(ratings(databases=1000), pool(), seed="s")
    assert picks[-1].kind == "mix"


def test_short_demo_lesson():
    picks = build_lesson(ratings(databases=1000, recursion=1050), pool(), seed="s", size=3)
    assert len(picks) == 3
    assert {p.topic for p in picks if p.kind == "focus"} == {"databases", "recursion"}
    assert sum(p.kind == "mix" for p in picks) == 1


def test_small_pool_does_not_crash():
    tiny = [Candidate("a", "caching", "system-design", 1100.0), Candidate("b", "binary-search", "debugging", 1250.0, "f")]
    picks = build_lesson(ratings(), tiny, seed="s")
    assert {p.question_id for p in picks} == {"a", "b"}
