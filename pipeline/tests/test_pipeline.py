import ast
import json

import pytest

from contracts.validate import VALIDATOR, semantic_errors
from pipeline import build, mutators, runner
from pipeline.cli import main

NAMES = build.corpus_names()


@pytest.mark.parametrize("name", NAMES)
def test_corpus_originals_pass_and_print_unchanged(name):
    source, cases = build.load(name)
    assert ast.unparse(ast.parse(source)) + "\n" == source
    assert len(cases.CASES) >= 4
    assert runner.run(source, cases.FUNCTION, cases.CASES).status == "pass"


def test_ten_plus_functions_cover_every_debugging_topic():
    topics = {build.load(n)[1].TOPIC for n in NAMES}
    assert topics == {"arrays-strings", "binary-search", "recursion", "sorting", "hash-maps"}
    assert len(NAMES) >= 10


@pytest.mark.parametrize("name", NAMES)
def test_every_mutant_changes_exactly_one_line(name):
    source, _ = build.load(name)
    original = source.rstrip("\n").split("\n")
    for m in mutators.generate(source):
        lines = m.source.split("\n")
        assert len(lines) == len(original)
        diff = [i for i, (a, b) in enumerate(zip(original, lines)) if a != b]
        assert diff == [m.line - 1]
        assert lines[m.line - 1] == m.mutated_line and original[m.line - 1] == m.original_line


def test_operators_cover_the_contract_list():
    ops = {m.operator for n in NAMES for m in mutators.generate(build.load(n)[0])}
    assert {"flip_comparison", "off_by_one", "wrong_operator", "wrong_base_case", "wrong_return", "swap_and_or"} <= ops


def test_no_unrealistic_zero_or_divisor_mutants():
    for n in NAMES:
        for m in mutators.generate(build.load(n)[0]):
            line = m.mutated_line
            assert "-0" not in line.replace(" ", "") or "-0." in line
            assert "+ 0" not in line and "// 1" not in line and "// 3" not in line and "% 3" not in line


def test_runner_reports_failures_without_tracebacks():
    src = "def f(x):\n    return x + 2\n"
    r = runner.run(src, "f", [((1,), 2), ((5,), 7)])
    assert r.status == "fail" and r.failure_text == "f(1): expected 2, got 3"


def test_runner_reports_exceptions_by_name_only():
    r = runner.run("def f(xs):\n    return xs[10]\n", "f", [(([1],), 1)])
    assert r.failure_text == "f([1]): raised IndexError"


def test_runner_times_out_infinite_loops():
    r = runner.run("def f():\n    while True:\n        pass\n", "f", [((), None)], timeout=0.5)
    assert r.status == "timeout"


def test_runner_does_not_let_mutation_of_args_leak_between_cases():
    src = "def f(xs):\n    xs.append(1)\n    return len(xs)\n"
    assert runner.run(src, "f", [(([],), 1), (([],), 1)]).status == "pass"


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("dbg") / "questions.json"
    questions, reports = build.build(out=out)
    return questions, reports, out


def test_build_emits_valid_verified_questions(built):
    questions, reports, _ = built
    assert not [r.error for r in reports if r.error]
    assert len(questions) >= 30
    for q in questions:
        assert not list(VALIDATOR.iter_errors(q)), q["id"]
        assert not semantic_errors(q), (q["id"], semantic_errors(q))
        lines = q["code"].split("\n")
        assert lines[q["answer"] - 1] == q["provenance"]["mutated_line"]
        assert q["provenance"]["tests_failed"] >= 1
        assert not build.leaks(q["code"], q["test_output"])
        assert "Traceback" not in q["test_output"] and 'File "' not in q["test_output"]


def test_build_verifies_by_rerunning(built):
    """Independently re-run a sample: buggy code fails, and fixing the answer line passes."""
    questions, _, _ = built
    for q in questions[::7]:
        name = q["provenance"]["source_function"].split("/")[-1].split(".py")[0]
        _, cases = build.load(name)
        assert runner.run(q["code"], cases.FUNCTION, cases.CASES).status == "fail"
        lines = q["code"].split("\n")
        lines[q["answer"] - 1] = q["provenance"]["original_line"]
        assert runner.run("\n".join(lines), cases.FUNCTION, cases.CASES).status == "pass"


def test_build_covers_topics_with_placement(built):
    questions, _, _ = built
    by_topic = {}
    for q in questions:
        by_topic.setdefault(q["topic"], []).append(q)
    assert len(by_topic) == 5
    for qs in by_topic.values():
        assert sum(bool(q.get("placement")) for q in qs) == 3


def test_build_is_deterministic(built, tmp_path):
    _, _, out = built
    again = tmp_path / "again.json"
    build.build(out=again)
    assert json.loads(out.read_text()) == json.loads(again.read_text())


def test_committed_questions_are_up_to_date(built):
    """content/debugging/questions.json must be the output of `python -m pipeline build`."""
    _, _, out = built
    assert json.loads(build.OUT.read_text()) == json.loads(out.read_text()), "run: python -m pipeline build"


def test_demo_cli_runs(capsys):
    assert main(["demo", "binary_search", "--fast", "--no-color"]) == 0
    text = capsys.readouterr().out
    assert "STEP 5" in text and "answer: line" in text
