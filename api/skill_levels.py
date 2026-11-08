"""Skill labels for presentation. Elo updates and learned ratings stay unchanged."""
BANDS = (
    ("level-1", 600), ("level-2", 1000), ("level-3", 1200),
    ("level-4", 1400), ("level-5", 1650), ("level-6", 1900), ("level-7", 2100),
)


def describe(rating: float) -> dict:
    index = max(i for i, (_, minimum) in enumerate(BANDS) if rating >= minimum) if rating >= 600 else 0
    name, minimum = BANDS[index]
    following = BANDS[index + 1] if index + 1 < len(BANDS) else None
    return {"level": name, "next_level": following[0] if following else None,
            "next_level_rating": following[1] if following else None,
            "level_progress": max(0, min(100, int((rating - minimum) / (following[1] - minimum) * 100))) if following else 100}


def metadata() -> list[dict]:
    return [{"id": name, "min_rating": minimum,
             "max_rating": BANDS[i + 1][1] - 1 if i + 1 < len(BANDS) else 2200}
            for i, (name, minimum) in enumerate(BANDS)]
