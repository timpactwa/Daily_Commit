import json
from pathlib import Path

import pytest

from api import db, skill_levels
from api.routes.placement import topic_levels
from api.routes.ranked import suggested_tier


@pytest.mark.parametrize("rating, expected", [
    (600, "level-1"), (999, "level-1"), (1000, "level-2"),
    (1199, "level-2"), (1200, "level-3"), (1399, "level-3"),
    (1400, "level-4"), (1649, "level-4"), (1650, "level-5"),
    (1899, "level-5"), (1900, "level-6"), (2099, "level-6"),
    (2100, "level-7"), (2200, "level-7"),
])
def test_boundaries(rating, expected):
    result = skill_levels.describe(rating)
    assert result["level"] == expected
    assert 0 <= result["level_progress"] <= 100


def test_advancement_requires_more_than_the_old_1300_threshold():
    levels = {r["topic"]: r for r in topic_levels({"caching": 1350, "scaling": 1650})}
    assert levels["caching"]["level"] == "level-3"
    assert levels["scaling"]["level"] == "level-5"
    assert skill_levels.describe(1600)["next_level_rating"] == 1650
    assert skill_levels.describe(2200)["next_level"] is None


def test_progress_and_ranked_suggestion_use_higher_thresholds(client, placed_user):
    uid = placed_user["X-User-Id"]
    with db.transaction() as conn:
        conn.execute("UPDATE user_topics SET rating = 1450 WHERE user_id = ?", (uid,))
        assert suggested_tier(conn, uid) == "intermediate"
    response = client.get("/v1/progress", headers=placed_user).json()
    assert len(response["skill_levels"]) == 7
    assert all(t["level"] == "level-4" and t["next_level_rating"] == 1650 for t in response["topics"])
    with db.transaction() as conn:
        conn.execute("UPDATE user_topics SET rating = 1650 WHERE user_id = ?", (uid,))
        assert suggested_tier(conn, uid) == "intermediate"
        conn.execute("UPDATE user_topics SET rating = 1900 WHERE user_id = ?", (uid,))
        assert suggested_tier(conn, uid) == "advanced"


def test_longer_modules_and_new_code_examples():
    root = Path(__file__).resolve().parents[2]
    modules = [json.loads(p.read_text(encoding="utf-8")) for p in (root / "content/learn").glob("*.json")]
    assert len(modules) == 10
    for module in modules:
        assert len(module["sections"]) == 4
        assert 10 <= module["minutes"] <= 20
        assert sum(len(" ".join(s["body"]).split()) for s in module["sections"]) >= 650
    examples = {s["id"]: s["example"]["code"] for m in modules for s in m["sections"]
                if s["id"] in {"sliding-window", "prefix-frequencies", "memoization", "verify-a-sort"}}
    scope = {}
    for code in examples.values():
        exec(compile(code, "learning-example", "exec"), scope)
    assert scope["longest_unique"]("abba") == 2
    assert scope["longest_unique"]("") == 0
    assert scope["count_subarrays"]([1, 1, 1], 2) == 2
    assert scope["count_subarrays"]([1, -1, 1], 1) == 3
    assert scope["fib"](10) == 55
    assert scope["fib"](0) == 0
    assert scope["valid_sort"]([2, 1, 1], [1, 1, 2])
    assert not scope["valid_sort"]([2, 1, 1], [1, 2])
