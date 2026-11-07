import pytest

from engine import elo

# (R, Q, context, answers_in_topic, attempts, S, R', Q') from contracts/rating.md
VECTORS = [
    (1200, 1200, "placement", 0, 0, 1, 1320.00, 1184.00),
    (1200, 1200, "placement", 0, 0, 0, 1080.00, 1216.00),
    (1200, 1050, "lesson", 3, 0, 0, 1166.24, 1072.51),
    (1400, 1250, "lesson", 15, 20, 1, 1407.12, 1245.25),
    (1200, 1400, "placement", 0, 0, 1, 1382.34, 1375.69),
]


@pytest.mark.parametrize("R,Q,ctx,n,att,S,R2,Q2", VECTORS)
def test_contract_vectors(R, Q, ctx, n, att, S, R2, Q2):
    u = elo.update(R, Q, S, ctx, n, att)
    assert round(u.student_after, 2) == R2
    assert round(u.question_after, 2) == Q2


def test_spillover_vector():
    u = elo.update(1200, 1400, 1, "placement")
    assert round(1200 + elo.SPILLOVER * u.student_delta, 2) == 1254.70


def test_k_schedule():
    assert elo.student_k("placement", 50) == 240
    assert elo.student_k("lesson", 9) == 48
    assert elo.student_k("lesson", 10) == 24
    assert elo.question_k(0) == 32
    assert elo.question_k(20) == 16
    assert elo.question_k(10_000) == 8


def test_clamped():
    assert elo.update(2190, 2200, 1, "placement").student_after == 2200
    assert elo.update(610, 600, 0, "placement").student_after == 600


def test_zero_sum_when_ks_equal():
    u = elo.update(1300, 1100, 1, "lesson", answers_in_topic=99, attempts=20)  # K_s=24, K_q=16
    assert u.student_after > 1300 and u.question_after < 1100


def test_bad_score_rejected():
    with pytest.raises(ValueError):
        elo.update(1200, 1200, 1.5)


@pytest.mark.parametrize("r,lvl,ready", [(1080, "beginner", 26), (1150, "intermediate", 36), (1320, "advanced", 60), (2000, "advanced", 100), (700, "beginner", 0)])
def test_level_and_readiness(r, lvl, ready):
    assert elo.level(r) == lvl
    assert elo.readiness(r) == ready


def test_target_difficulty_is_about_70_percent():
    assert abs(elo.expected(1300, elo.target_difficulty(1300)) - 0.70) < 0.01
