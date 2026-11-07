"""Grade a response against a question's answer. Rules in contracts/rating.md ("Scoring")."""
from typing import Any


class InvalidResponse(ValueError):
    """Response shape does not match the question format (API maps this to 422)."""


def score(fmt: str, response: Any, answer: Any) -> float:
    """Return S in [0, 1]. Correct means S == 1."""
    if fmt in ("mcq", "predict_output", "tap_node"):
        if not isinstance(response, str):
            raise InvalidResponse(f"{fmt} expects an option/node id string")
        return 1.0 if response == answer else 0.0

    if fmt == "tap_line":
        if isinstance(response, bool) or not isinstance(response, int) or response < 1:
            raise InvalidResponse("tap_line expects a 1-indexed line number")
        return 1.0 if response == answer else 0.0

    if fmt == "reorder":
        if not isinstance(response, list) or not all(isinstance(x, str) for x in response):
            raise InvalidResponse("reorder expects a list of option ids")
        if sorted(response) != sorted(answer):
            raise InvalidResponse("reorder response must contain each option id exactly once")
        return pair_agreement(response, answer)

    raise InvalidResponse(f"unknown format {fmt!r}")


def pair_agreement(response: list[str], answer: list[str]) -> float:
    """Fraction of item pairs in the correct relative order (Kendall agreement), 2 dp."""
    pos = {item: i for i, item in enumerate(answer)}
    n = len(response)
    total = n * (n - 1) // 2
    if total == 0:
        return 1.0
    agree = sum(
        1 for i in range(n) for j in range(i + 1, n) if pos[response[i]] < pos[response[j]]
    )
    return round(agree / total, 2)
