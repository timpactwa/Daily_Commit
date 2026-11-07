"""Run a function's case table against some source in an isolated subprocess.

The child prints one JSON result per case. Failure text is written here, never a traceback,
so the output cannot quote the buggy line (the answer):
    search([1, 3, 5, 7], 7): expected 3, got -1
    factorial(0): raised RecursionError
"""
import json
import subprocess
import sys
from dataclasses import dataclass

# Allow interpreter startup under load as well as the tiny case tables. A short
# startup race must not change which mutants enter the generated question bank.
TIMEOUT_S = 3.0

_CHILD = r"""
import copy, json, sys
sys.setrecursionlimit(300)
payload = json.loads(sys.stdin.read())
ns = {}
exec(payload["source"], ns)
fn = ns[payload["function"]]
out = []
for args, expected in payload["cases"]:
    call = payload["function"] + "(" + ", ".join(repr(a) for a in args) + ")"
    try:
        got = fn(*copy.deepcopy(args))
        out.append({"call": call, "ok": got == expected, "expected": repr(expected), "got": repr(got)})
    except BaseException as e:
        out.append({"call": call, "ok": False, "expected": repr(expected), "error": type(e).__name__})
print(json.dumps(out))
"""


@dataclass(frozen=True)
class RunResult:
    status: str                 # "pass" | "fail" | "timeout" | "crash"
    total: int
    failed: list[dict]

    @property
    def failure_text(self) -> str:
        lines = []
        for r in self.failed:
            if "error" in r:
                lines.append(f"{r['call']}: raised {r['error']}")
            else:
                lines.append(f"{r['call']}: expected {r['expected']}, got {r['got']}")
        return "\n".join(lines)


def _jsonable(cases: list) -> list:
    return [[list(args), expected] for args, expected in cases]


def run(source: str, function: str, cases: list, timeout: float = TIMEOUT_S) -> RunResult:
    payload = json.dumps({"source": source, "function": function, "cases": _jsonable(cases)})
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", _CHILD],
            input=payload, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return RunResult("timeout", len(cases), [])
    if proc.returncode != 0:
        return RunResult("crash", len(cases), [])
    results = json.loads(proc.stdout)
    failed = [r for r in results if not r["ok"]]
    return RunResult("fail" if failed else "pass", len(results), failed)


def run_many(source_list: list[str], function: str, cases: list, workers: int = 8) -> list[RunResult]:
    """Run several sources concurrently (each in its own subprocess), results in input order."""
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda src: run(src, function, cases), source_list))
