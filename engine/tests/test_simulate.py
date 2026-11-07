"""Regression guard on engine behavior using the simulation (small run, ~1 s)."""
import statistics

from engine import simulate


def test_engine_learns_and_keeps_lessons_winnable():
    r = simulate.run(students=60, days=10, seed=3)
    err = r["student_error"]
    assert err[-1] < err[0] - 20, "student ratings should move toward true skill"
    assert r["question_error_end"] < r["question_error_start"] * 0.7, "question ratings should calibrate"
    late = statistics.fmean(r["success"][-3:])
    assert late >= 0.52, f"lessons got too hard over time ({late:.0%})"
