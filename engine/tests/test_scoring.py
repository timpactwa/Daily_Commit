import pytest

from engine.scoring import InvalidResponse, pair_agreement, score


def test_choice_formats():
    for fmt in ("mcq", "predict_output", "tap_node"):
        assert score(fmt, "b", "b") == 1.0
        assert score(fmt, "a", "b") == 0.0


def test_tap_line():
    assert score("tap_line", 3, 3) == 1.0
    assert score("tap_line", 4, 3) == 0.0


@pytest.mark.parametrize("fmt,resp", [("mcq", 2), ("tap_line", "3"), ("tap_line", True), ("tap_line", 0), ("tap_node", None), ("reorder", "s1")])
def test_wrong_shape(fmt, resp):
    with pytest.raises(InvalidResponse):
        score(fmt, resp, "x" if fmt != "reorder" else ["s1", "s2"])


def test_reorder_exact_and_partial():
    ans = ["s1", "s2", "s3", "s4", "s5"]
    assert score("reorder", ans, ans) == 1.0
    assert score("reorder", list(reversed(ans)), ans) == 0.0
    # one adjacent swap breaks 1 of 10 pairs
    assert score("reorder", ["s2", "s1", "s3", "s4", "s5"], ans) == 0.9


def test_reorder_must_be_permutation():
    with pytest.raises(InvalidResponse):
        score("reorder", ["s1", "s1", "s3"], ["s1", "s2", "s3"])


def test_pair_agreement_rounding():
    assert pair_agreement(["b", "a", "c"], ["a", "b", "c"]) == 0.67


def test_unknown_format():
    with pytest.raises(InvalidResponse):
        score("essay", "x", "x")
