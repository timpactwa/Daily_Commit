"""Corpus -> verified debugging questions (content/debugging/questions.json).

For each corpus function:
  1. The original must pass every case (otherwise the function is skipped and reported).
  2. Generate single-line mutants (pipeline.mutators).
  3. Run each mutant's cases in a sandboxed subprocess (pipeline.runner).
  4. Keep a mutant only if at least one case FAILS. Passing (equivalent) mutants, timeouts
     (infinite loops) and crashes are discarded.
  5. Drop mutants whose failure text duplicates another's, and any whose output would
     reveal a line of code (leak check).
  6. Emit a tap_line question with provenance.
"""
import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from pipeline import mutators, runner

ROOT = Path(__file__).resolve().parent.parent
CORPUS = Path(__file__).resolve().parent / "corpus"
OUT = ROOT / "content" / "debugging" / "questions.json"

MAX_PER_FUNCTION = 6
MAX_FAILURE_LINES = 3
OPERATOR_ORDER = ["flip_comparison", "off_by_one", "wrong_base_case", "wrong_operator", "wrong_return", "swap_and_or"]
SEED_BASE = {
    "flip_comparison": 975, "wrong_operator": 1025, "wrong_base_case": 1025,
    "wrong_return": 1025, "swap_and_or": 1075, "off_by_one": 1125,
}
PHRASE = {
    "flip_comparison": "the comparison was flipped",
    "off_by_one": "a number is off by one",
    "wrong_operator": "it uses the wrong operator",
    "swap_and_or": "`and` and `or` were swapped",
    "wrong_base_case": "the base case is wrong",
    "wrong_return": "it returns the wrong value",
}
PLACEMENT_TARGETS = (1000, 1200, 1400)


@dataclass(frozen=True)
class Corpus:
    """Where a set of corpus functions lives and how its questions are labelled.

    `path=None` means the lesson corpus directory `CORPUS`, looked up at call time.
    """
    package: str                 # importable package holding the <name>_cases modules
    source_prefix: str           # repo-relative dir written into provenance.source_function
    id_prefix: str = "dbg"
    path: Path | None = None

    @property
    def dir(self) -> Path:
        return self.path if self.path is not None else CORPUS


LESSONS = Corpus("pipeline.corpus", "pipeline/corpus")


@dataclass
class FunctionReport:
    name: str
    topic: str
    mutants: int = 0
    killed: int = 0
    survived: int = 0      # tests still pass: equivalent or untested, discarded
    timeouts: int = 0
    crashes: int = 0
    duplicates: int = 0
    leaks: int = 0
    kept: list[dict] = field(default_factory=list)
    error: str | None = None


def corpus_names(corpus: Corpus = LESSONS) -> list[str]:
    return sorted(p.stem[: -len("_cases")] for p in corpus.dir.glob("*_cases.py"))


def load(name: str, corpus: Corpus = LESSONS) -> tuple[str, object]:
    # Normalize line endings: Windows checkouts may convert corpus files to CRLF.
    source = (corpus.dir / f"{name}.py").read_text(encoding="utf-8").replace("\r\n", "\n")
    cases = importlib.import_module(f"{corpus.package}.{name}_cases")
    return source, cases


def leaks(code: str, output: str) -> bool:
    return any(len(ln.strip()) > 8 and ln.strip() in output for ln in code.split("\n"))


def difficulty(operator: str, code: str) -> int:
    return max(600, min(2200, SEED_BASE[operator] + 10 * (len(code.split("\n")) - 8)))


def make_question(name: str, cases, m: mutators.Mutant, result: runner.RunResult, number: int,
                  corpus: Corpus = LESSONS) -> dict:
    failure_lines = result.failure_text.split("\n")[:MAX_FAILURE_LINES]
    first_call = result.failed[0]["call"]
    question = {
        "id": f"{corpus.id_prefix}-{name.replace('_', '-')}-{m.operator.replace('_', '-')}-{number:02d}",
        "version": 1,
        "track": "debugging",
        "topic": cases.TOPIC,
        "format": "tap_line",
        "prompt": getattr(cases, "PROMPT", "This function fails the tests below. Tap the buggy line."),
        "code": m.source,
        "language": "python",
        "test_output": "\n".join(failure_lines),
        "answer": m.line,
        "explanation": f"Line {m.line} should be `{m.original_line.strip()}`, but {PHRASE[m.operator]}. That is why {first_call} fails.",
        "difficulty_rating": max(600, min(2200, difficulty(m.operator, m.source) + getattr(cases, "DIFFICULTY_OFFSET", 0))),
        "provenance": {
            "source_function": f"{corpus.source_prefix}/{name}.py::{cases.FUNCTION}",
            "mutation_operator": m.operator,
            "original_line": m.original_line,
            "mutated_line": m.mutated_line,
            "tests_failed": len(result.failed),
            "tests_total": result.total,
        },
    }
    if edition := getattr(cases, "EDITION", None):
        question["tags"] = [edition, "verified-code"]
    return question


def process(name: str, corpus: Corpus = LESSONS, max_per_function: int = MAX_PER_FUNCTION) -> FunctionReport:
    source, cases = load(name, corpus)
    report = FunctionReport(name, cases.TOPIC)
    limit = getattr(cases, "QUESTION_LIMIT", MAX_PER_FUNCTION)
    if type(limit) is not int or not 1 <= limit <= MAX_PER_FUNCTION:
        report.error = f"QUESTION_LIMIT must be an integer in 1..{MAX_PER_FUNCTION}"
        return report
    original = runner.run(source, cases.FUNCTION, cases.CASES)
    if original.status != "pass":
        report.error = f"original does not pass its cases ({original.status}): {original.failure_text}"
        return report

    ms = mutators.generate(source)
    report.mutants = len(ms)
    results = runner.run_many([m.source for m in ms], cases.FUNCTION, cases.CASES)
    candidates, seen_failures = [], set()
    for m, r in zip(ms, results):
        if r.status == "pass":
            report.survived += 1
            continue
        if r.status == "timeout":
            report.timeouts += 1
            continue
        if r.status == "crash":
            report.crashes += 1
            continue
        report.killed += 1
        text = "\n".join(r.failure_text.split("\n")[:MAX_FAILURE_LINES])
        if text in seen_failures:
            report.duplicates += 1
            continue
        if leaks(m.source, text):
            report.leaks += 1
            continue
        seen_failures.add(text)
        candidates.append((m, r))

    # Round-robin across operators so each function contributes a variety of bug types.
    by_op: dict[str, list] = {}
    for m, r in candidates:
        by_op.setdefault(m.operator, []).append((m, r))
    chosen = []
    limit = min(limit, max_per_function)
    while len(chosen) < limit and any(by_op.values()):
        for op in OPERATOR_ORDER:
            if by_op.get(op) and len(chosen) < limit:
                chosen.append(by_op[op].pop(0))
    counters: dict[str, int] = {}
    for m, r in chosen:
        counters[m.operator] = counters.get(m.operator, 0) + 1
        report.kept.append(make_question(name, cases, m, r, counters[m.operator], corpus))
    return report


def tag_placement(questions: list[dict]) -> None:
    """Per topic, flag the questions closest to 1000 / 1200 / 1400 for the placement test."""
    by_topic: dict[str, list[dict]] = {}
    for q in questions:
        by_topic.setdefault(q["topic"], []).append(q)
    for qs in by_topic.values():
        used: set[str] = set()
        for target in PLACEMENT_TARGETS:
            pick = min((q for q in qs if q["id"] not in used), key=lambda q: (abs(q["difficulty_rating"] - target), q["id"]), default=None)
            if pick:
                used.add(pick["id"])
                pick["placement"] = True


def build(names: list[str] | None = None, out: Path = OUT) -> tuple[list[dict], list[FunctionReport]]:
    reports = [process(n) for n in (names or corpus_names())]
    questions = [q for r in reports for q in r.kept]
    tag_placement(questions)
    questions.sort(key=lambda q: q["id"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(questions, indent=2) + "\n", encoding="utf-8")
    return questions, reports
