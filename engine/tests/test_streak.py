from engine.streak import Streak, complete, visible


def test_first_lesson_starts_at_one():
    s, ext = complete(Streak(0, 0, None), "2026-11-08")
    assert s == Streak(1, 1, "2026-11-08") and ext


def test_consecutive_day_extends():
    s, ext = complete(Streak(6, 6, "2026-11-07"), "2026-11-08")
    assert s == Streak(7, 7, "2026-11-08") and ext


def test_same_day_is_idempotent():
    start = Streak(3, 5, "2026-11-08")
    assert complete(start, "2026-11-08") == (start, False)


def test_gap_resets_but_keeps_best():
    s, ext = complete(Streak(5, 9, "2026-11-05"), "2026-11-08")
    assert s == Streak(1, 9, "2026-11-08") and ext


def test_month_boundary():
    assert complete(Streak(2, 2, "2026-10-31"), "2026-11-01")[0].current == 3


def test_visible_streak():
    s = Streak(4, 4, "2026-11-07")
    assert visible(s, "2026-11-07") == 4
    assert visible(s, "2026-11-08") == 4  # still alive, today not done yet
    assert visible(s, "2026-11-09") == 0  # broken
