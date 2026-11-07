"""Elo rating updates. Pure functions; constants and vectors in contracts/rating.md."""
from dataclasses import dataclass
from typing import Literal

R0 = 1200.0
K_PLACEMENT = 240.0
K_NEW = 48.0
K_SETTLED = 24.0
NEW_ANSWERS = 10
K_Q_MAX = 32.0
K_Q_MIN = 8.0
R_MIN, R_MAX = 600.0, 2200.0
TARGET_GAP = 150.0
SPILLOVER = 0.3

Context = Literal["placement", "lesson"]


def clamp(r: float) -> float:
    return max(R_MIN, min(R_MAX, r))


def expected(student: float, question: float) -> float:
    """Expected score for a student rated `student` on a question rated `question`."""
    return 1.0 / (1.0 + 10.0 ** ((question - student) / 400.0))


def student_k(context: Context, answers_in_topic: int) -> float:
    if context == "placement":
        return K_PLACEMENT
    return K_NEW if answers_in_topic < NEW_ANSWERS else K_SETTLED


def question_k(attempts: int) -> float:
    return max(K_Q_MIN, K_Q_MAX / (1.0 + attempts / 20.0))


@dataclass(frozen=True)
class Update:
    student_before: float
    student_after: float
    question_before: float
    question_after: float
    expected: float
    score: float

    @property
    def student_delta(self) -> float:
        """Raw (unclamped-by-display) change, used for placement spillover."""
        return self.student_after - self.student_before


def update(
    student: float,
    question: float,
    score: float,
    context: Context = "lesson",
    answers_in_topic: int = 0,
    attempts: int = 0,
) -> Update:
    """Apply one answer. `score` is S in [0, 1] from engine.scoring."""
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"score must be in [0, 1], got {score}")
    e = expected(student, question)
    surprise = score - e
    return Update(
        student_before=student,
        student_after=clamp(student + student_k(context, answers_in_topic) * surprise),
        question_before=question,
        question_after=clamp(question - question_k(attempts) * surprise),
        expected=e,
        score=score,
    )


def target_difficulty(student: float) -> float:
    """Question rating a lesson aims for (~70% expected success)."""
    return student - TARGET_GAP


def level(rating: float) -> str:
    if rating < 1150:
        return "beginner"
    return "intermediate" if rating < 1300 else "advanced"


def readiness(rating: float) -> int:
    return max(0, min(100, round((rating - 900) / 700 * 100)))
