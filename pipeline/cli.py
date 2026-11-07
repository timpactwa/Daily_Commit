"""python -m pipeline {build,check,demo}

  build             generate content/debugging/questions.json from the corpus
  check             verify every corpus function passes its cases and prints unchanged
  demo <function>   live walkthrough for the stage demo (e.g. binary_search)
"""
import argparse
import ast
import json
import re
import sys
import time

from pipeline import build, mutators, runner

GREEN, RED, YELLOW, CYAN, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[2m", "\033[1m", "\033[0m"


def cmd_build(_: argparse.Namespace) -> int:
    t = time.time()
    questions, reports = build.build()
    print(f"{'function':16} {'mutants':>7} {'killed':>6} {'survived':>8} {'timeout':>7} {'dup':>4} {'kept':>4}")
    for r in reports:
        if r.error:
            print(f"{r.name:16} ERROR {r.error}")
            continue
        print(f"{r.name:16} {r.mutants:7} {r.killed:6} {r.survived:8} {r.timeouts:7} {r.duplicates:4} {len(r.kept):4}")
    topics: dict[str, int] = {}
    for q in questions:
        topics[q["topic"]] = topics.get(q["topic"], 0) + 1
    print(f"\n{len(questions)} verified questions -> {build.OUT.relative_to(build.ROOT)} ({time.time() - t:.1f}s)")
    print("by topic: " + ", ".join(f"{k} {v}" for k, v in sorted(topics.items())))
    return 1 if any(r.error for r in reports) else 0


def cmd_check(_: argparse.Namespace) -> int:
    bad = 0
    for name in build.corpus_names():
        source, cases = build.load(name)
        printed = ast.unparse(ast.parse(source)) + "\n"
        r = runner.run(source, cases.FUNCTION, cases.CASES)
        problems = []
        if printed != source:
            problems.append("source changes when printed (write it the way ast.unparse prints it)")
        if r.status != "pass":
            problems.append(f"cases {r.status}: {r.failure_text}")
        if len(cases.CASES) < 4:
            problems.append("needs at least 4 cases")
        bad += bool(problems)
        print(f"{name:16} {'OK' if not problems else 'FAIL ' + '; '.join(problems)}")
    return 1 if bad else 0


class Out:
    """Prints to the terminal with color, and optionally records a plain-text copy."""

    def __init__(self, color: bool, record: bool):
        self.color, self.lines = color, [] if record else None

    def __call__(self, text: str = "", style: str = "") -> None:
        print(f"{style}{text}{RESET}" if self.color and style else text)
        if self.lines is not None:
            self.lines.append(re.sub(r"\033\[[0-9;]*m", "", text))


def show_code(out: Out, code: str, mark: int | None = None, style: str = "") -> None:
    for i, line in enumerate(code.split("\n"), 1):
        pointer = ">>" if i == mark else "  "
        out(f"  {i:2} {pointer} {line}", (RED + BOLD) if i == mark else style)


def cmd_demo(a: argparse.Namespace) -> int:
    pause = (lambda s: None) if a.fast else time.sleep
    out = Out(color=sys.stdout.isatty() and not a.no_color, record=bool(a.save))
    if a.function not in build.corpus_names():
        print(f"unknown function {a.function!r}; choose from: {', '.join(build.corpus_names())}")
        return 2
    source, cases = build.load(a.function)

    out("STEP 1  A working function and its tests", BOLD + CYAN)
    show_code(out, source.rstrip("\n"))
    pause(1.5)
    ok = runner.run(source, cases.FUNCTION, cases.CASES)
    out(f"  running {ok.total} test cases ... {'all pass' if ok.status == 'pass' else ok.status}", GREEN if ok.status == "pass" else RED)
    if ok.status != "pass":
        return 1
    pause(1.5)

    out()
    out("STEP 2  Generate every single-line bug", BOLD + CYAN)
    ms = mutators.generate(source)
    results = runner.run_many([m.source for m in ms], cases.FUNCTION, cases.CASES)
    survived = sum(r.status == "pass" for r in results)
    hung = sum(r.status == "timeout" for r in results)
    out(f"  {len(ms)} candidate bugs: {len(ms) - survived - hung} break a test, "
        f"{survived} don't (thrown away), {hung} loop forever (thrown away)")
    pause(1.5)

    preferred = [a.operator] if a.operator else ["flip_comparison", "off_by_one", "wrong_operator", "wrong_base_case"]
    pick = next(((m, r) for op in preferred for m, r in zip(ms, results) if m.operator == op and r.status == "fail"), None)
    if pick is None:
        out("  no failing mutant found", RED)
        return 1
    m, r = pick
    out()
    out(f"STEP 3  Inject one bug ({m.operator.replace('_', ' ')})", BOLD + CYAN)
    out(f"  line {m.line}:  {m.original_line.strip()}", GREEN)
    out(f"      ->   {m.mutated_line.strip()}", RED)
    pause(1.5)

    out()
    out("STEP 4  Run the same tests: the bug must make them fail", BOLD + CYAN)
    out(f"  {len(r.failed)} of {r.total} cases fail  ->  bug is real, keep it", YELLOW)
    for line in r.failure_text.split("\n")[: build.MAX_FAILURE_LINES]:
        out(f"    {line}", RED)
    pause(2)

    out()
    out("STEP 5  Emit the question (answer = the line we changed)", BOLD + CYAN)
    q = build.make_question(a.function, cases, m, r, 1)
    show_code(out, q["code"], mark=q["answer"])
    out(f"  answer: line {q['answer']}   difficulty: {q['difficulty_rating']}   id: {q['id']}", DIM)
    if a.json:
        out(json.dumps(q, indent=2))

    if a.save:
        from pathlib import Path

        Path(a.save).write_text("\n".join(out.lines) + "\n", encoding="utf-8")
        print(f"\n(saved to {a.save})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m pipeline", description="Verified bug pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="generate content/debugging/questions.json").set_defaults(fn=cmd_build)
    sub.add_parser("check", help="verify the corpus").set_defaults(fn=cmd_check)
    d = sub.add_parser("demo", help="live walkthrough for one corpus function")
    d.add_argument("function", nargs="?", default="binary_search")
    d.add_argument("--operator", help="prefer this mutation operator")
    d.add_argument("--fast", action="store_true", help="no pauses")
    d.add_argument("--no-color", action="store_true")
    d.add_argument("--json", action="store_true", help="also print the question JSON")
    d.add_argument("--save", help="write a plain-text copy of the output to this file")
    d.set_defaults(fn=cmd_demo)
    a = ap.parse_args(argv)
    return a.fn(a)
