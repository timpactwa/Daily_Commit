"""Ranked corpus -> verified debugging questions for the ranked tests (content/ranked/debugging.json).

Reuses the lesson machinery in pipeline.build (load, mutate, run, kill check, timeout/crash
filter, dedupe, leak check) on a separate corpus, pipeline/ranked_corpus, whose functions never
appear in lessons. Each corpus function declares a TIER; every tier gets exactly
QUESTIONS_PER_TIER questions, one per function where possible, spread across operators.
"""
import json
import re
from pathlib import Path

from pipeline import build

RANKED_CORPUS = Path(__file__).resolve().parent / "ranked_corpus"
OUT = build.ROOT / "content" / "ranked" / "debugging.json"
RANKED = build.Corpus("pipeline.ranked_corpus", "pipeline/ranked_corpus", id_prefix="dbg-ranked", path=RANKED_CORPUS)

TIERS = ("beginner", "intermediate", "advanced")
BANDS = {"beginner": (850, 990), "intermediate": (1050, 1280), "advanced": (1320, 1500)}
QUESTIONS_PER_TIER = 5
CANDIDATES_PER_FUNCTION = 12
RAW_LO, RAW_HI = 900, 1300


def tier_rating(raw: int, tier: str) -> int:
    """Map the lesson difficulty() heuristic into the tier's band.

    The lesson heuristic gives SEED_BASE[operator] + 10 * (lines - 8); for ranked corpus
    functions that lands roughly in 900..1300. Clamp raw to [RAW_LO, RAW_HI] and map it
    linearly onto the tier band [lo, hi]:

        rating = lo + round((clamp(raw, 900, 1300) - 900) * (hi - lo) / 400)

    so harder operators and longer code still rank higher within a tier, and every rating
    falls inside its band (beginner 850..990, intermediate 1050..1280, advanced 1320..1500).
    """
    lo, hi = BANDS[tier]
    raw = max(RAW_LO, min(RAW_HI, raw))
    return lo + round((raw - RAW_LO) * (hi - lo) / (RAW_HI - RAW_LO))


def ranked_names() -> list[str]:
    return build.corpus_names(RANKED)


def load(name: str) -> tuple[str, object]:
    return build.load(name, RANKED)


def _weak(q: dict, tier: str) -> bool:
    """Bugs that test little: a bare `return <int>` nudged by one (return -1 -> -2), a no-op
    step (`+= 0`), a type error on every failing case (e.g. list `-=`), and, for the advanced
    tier, tweaks to the first setup lines instead of the core logic."""
    original = q["provenance"]["original_line"].strip()
    mutated = q["provenance"]["mutated_line"]
    failures = q["test_output"].split("\n")
    return (
        re.fullmatch(r"return -?\d+", original) is not None
        or re.search(r"[+-]= 0\b", mutated) is not None
        or all(f.endswith("raised TypeError") for f in failures)
        or (tier == "advanced" and q["answer"] <= 3)
    )


def _pick(reports: list[build.FunctionReport], used_ops: dict[str, int], tier: str) -> list[dict]:
    """One question per function (round-robin if a tier has fewer functions than slots).
    Within a function: avoid weak bugs, then prefer the operator used least so far across
    all tiers, then OPERATOR_ORDER, then id (deterministic)."""
    pools = {r.name: list(r.kept) for r in reports if not r.error}
    chosen: list[dict] = []
    while len(chosen) < QUESTIONS_PER_TIER and any(pools.values()):
        for name in sorted(pools):
            if len(chosen) >= QUESTIONS_PER_TIER or not pools[name]:
                continue
            q = min(
                pools[name],
                key=lambda q: (
                    _weak(q, tier),
                    used_ops.get(q["provenance"]["mutation_operator"], 0),
                    build.OPERATOR_ORDER.index(q["provenance"]["mutation_operator"]),
                    q["id"],
                ),
            )
            pools[name].remove(q)
            used_ops[q["provenance"]["mutation_operator"]] = used_ops.get(q["provenance"]["mutation_operator"], 0) + 1
            chosen.append(q)
    return chosen


def build_ranked(out: Path = OUT) -> tuple[list[dict], list[build.FunctionReport], dict[str, list[str]]]:
    """Build the ranked debugging questions. Returns (questions, reports, tier -> ids)."""
    reports: list[build.FunctionReport] = []
    tiers: dict[str, list[str]] = {}
    questions: list[dict] = []
    used_ops: dict[str, int] = {}
    for tier in TIERS:
        names = [n for n in ranked_names() if load(n)[1].TIER == tier]
        tier_reports = [build.process(n, RANKED, CANDIDATES_PER_FUNCTION) for n in names]
        reports += tier_reports
        picked = _pick(tier_reports, used_ops, tier)
        for q in picked:
            q["difficulty_rating"] = tier_rating(q["difficulty_rating"], tier)
        picked.sort(key=lambda q: (q["difficulty_rating"], q["id"]))
        tiers[tier] = [q["id"] for q in picked]
        questions += picked
    ids = {q["id"] for q in questions}
    for r in reports:  # report only what was actually emitted
        r.kept = [q for q in r.kept if q["id"] in ids]
    questions.sort(key=lambda q: q["id"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(questions, indent=2) + "\n", encoding="utf-8")
    return questions, reports, tiers
