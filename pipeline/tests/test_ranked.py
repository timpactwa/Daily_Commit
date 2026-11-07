import ast
import json
import re

import pytest

from contracts.validate import VALIDATOR, semantic_errors
from pipeline import build, ranked, runner
from pipeline.cli import main

NAMES = ranked.ranked_names()


@pytest.mark.parametrize("name", NAMES)
def test_ranked_originals_pass_and_print_unchanged(name):
    source, cases = ranked.load(name)
    assert ast.unparse(ast.parse(source)) + "\n" == source
    assert len(cases.CASES) >= 5
    assert cases.TIER in ranked.TIERS
    assert runner.run(source, cases.FUNCTION, cases.CASES).status == "pass"


def test_ranked_corpus_is_new_and_covers_every_topic_per_tier_set():
    assert not set(NAMES) & set(build.corpus_names())
    lesson_sources = {build.load(n)[0] for n in build.corpus_names()}
    assert not {ranked.load(n)[0] for n in NAMES} & lesson_sources
    topics = {ranked.load(n)[1].TOPIC for n in NAMES}
    assert topics == {"arrays-strings", "binary-search", "recursion", "sorting", "hash-maps"}
    for tier in ranked.TIERS:
        assert sum(ranked.load(n)[1].TIER == tier for n in NAMES) >= ranked.QUESTIONS_PER_TIER


@pytest.mark.parametrize("raw", range(500, 2300, 25))
@pytest.mark.parametrize("tier", ranked.TIERS)
def test_tier_rating_stays_in_band(tier, raw):
    lo, hi = ranked.BANDS[tier]
    assert lo <= ranked.tier_rating(raw, tier) <= hi


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("ranked") / "debugging.json"
    questions, reports, tiers = ranked.build_ranked(out=out)
    return questions, reports, tiers, out


def test_ranked_build_has_five_per_tier_in_band(built):
    questions, reports, tiers, _ = built
    assert not [r.error for r in reports if r.error]
    assert len(questions) == 15
    assert list(tiers) == list(ranked.TIERS)
    by_id = {q["id"]: q for q in questions}
    assert sorted(i for ids in tiers.values() for i in ids) == sorted(by_id)
    for tier, ids in tiers.items():
        assert len(ids) == 5
        lo, hi = ranked.BANDS[tier]
        fns = set()
        for qid in ids:
            q = by_id[qid]
            assert lo <= q["difficulty_rating"] <= hi, (qid, q["difficulty_rating"])
            name = q["provenance"]["source_function"].split("/")[-1].split(".py")[0]
            assert ranked.load(name)[1].TIER == tier
            fns.add(name)
        assert len(fns) == 5, f"{tier}: one question per function"


def test_ranked_questions_are_valid_and_verified(built):
    questions, _, _, _ = built
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids))
    for q in questions:
        assert re.fullmatch(r"dbg-ranked-[a-z0-9-]+", q["id"])
        assert "placement" not in q
        assert not list(VALIDATOR.iter_errors(q)), q["id"]
        assert not semantic_errors(q), (q["id"], semantic_errors(q))
        assert q["provenance"]["source_function"].startswith("pipeline/ranked_corpus/")
        lines = q["code"].split("\n")
        assert lines[q["answer"] - 1] == q["provenance"]["mutated_line"]
        assert not build.leaks(q["code"], q["test_output"])
        assert "Traceback" not in q["test_output"]
        # Re-run: the buggy code fails, and restoring the original line passes.
        name = q["provenance"]["source_function"].split("/")[-1].split(".py")[0]
        _, cases = ranked.load(name)
        assert runner.run(q["code"], cases.FUNCTION, cases.CASES).status == "fail"
        lines[q["answer"] - 1] = q["provenance"]["original_line"]
        assert runner.run("\n".join(lines), cases.FUNCTION, cases.CASES).status == "pass"


def test_ranked_varies_operators(built):
    questions, _, _, _ = built
    assert len({q["provenance"]["mutation_operator"] for q in questions}) >= 5


def test_ranked_build_is_deterministic(built, tmp_path):
    _, _, tiers, out = built
    again = tmp_path / "again.json"
    _, _, tiers2 = ranked.build_ranked(out=again)
    assert out.read_text() == again.read_text()
    assert tiers == tiers2


def test_committed_ranked_questions_are_up_to_date(built):
    """content/ranked/debugging.json must be the output of `python -m pipeline ranked`."""
    _, _, _, out = built
    assert json.loads(ranked.OUT.read_text()) == json.loads(out.read_text()), "run: python -m pipeline ranked"


def test_ranked_does_not_touch_lesson_output(built):
    """Lesson questions keep their ids/paths and never come from the ranked corpus."""
    lessons = json.loads(build.OUT.read_text())
    assert all(not q["id"].startswith("dbg-ranked-") for q in lessons)
    assert all(q["provenance"]["source_function"].startswith("pipeline/corpus/") for q in lessons)
    assert ranked.OUT != build.OUT


def test_check_cli_covers_ranked_corpus(capsys):
    assert main(["check"]) == 0
    text = capsys.readouterr().out
    assert all(f"ranked/{n}" in text for n in NAMES)
