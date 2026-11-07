"""Validate question content against the shared contracts.

Usage (from repo root):
    pip install jsonschema
    python contracts/validate.py                      # all content/**/*.json + contracts/examples
    python contracts/validate.py path/to/file.json    # specific files

Checks: JSON schema, topic id exists and matches track, unique ids,
answer refers to a real option/node/line, reorder answer is a permutation.
Exit code 1 on any error. CI runs this on every PR.
"""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "contracts" / "question.schema.json").read_text(encoding="utf-8"))
TOPICS = {t["id"]: t["track"] for t in json.loads((ROOT / "contracts" / "topics.json").read_text(encoding="utf-8"))["topics"]}
VALIDATOR = Draft202012Validator(SCHEMA)
NON_QUESTION_FILES = {"showcase.json", "demo-user.json"}


def semantic_errors(q):
    errs = []
    if TOPICS.get(q["topic"]) != q["track"]:
        errs.append(f"topic '{q['topic']}' unknown or not in track '{q['track']}'")
    fmt, ans = q["format"], q["answer"]
    option_ids = [o["id"] for o in q.get("options", [])]
    if len(option_ids) != len(set(option_ids)):
        errs.append("duplicate option ids")
    if fmt in ("mcq", "predict_output") and ans not in option_ids:
        errs.append(f"answer '{ans}' is not an option id")
    if fmt == "tap_line":
        lines = q["code"].split("\n")
        if not (isinstance(ans, int) and 1 <= ans <= len(lines)):
            errs.append(f"answer line {ans} outside 1..{len(lines)}")
        out = q.get("test_output", "")
        for ln in lines:
            if ln.strip() and len(ln.strip()) > 8 and ln.strip() in out:
                errs.append(f"test_output leaks a code line: '{ln.strip()}'")
        prov = q.get("provenance")
        if prov and isinstance(ans, int) and 1 <= ans <= len(lines) and prov["mutated_line"] != lines[ans - 1]:
            errs.append("provenance.mutated_line does not match the answer line")
    if fmt == "reorder" and sorted(ans) != sorted(option_ids):
        errs.append("reorder answer is not a permutation of option ids")
    if fmt == "tap_node":
        node_ids = {n["id"] for n in q["diagram"]["nodes"]}
        if ans not in node_ids:
            errs.append(f"answer '{ans}' is not a node id")
        for e in q["diagram"]["edges"]:
            if e["from"] not in node_ids or e["to"] not in node_ids:
                errs.append(f"edge {e['from']}->{e['to']} references unknown node")
    return errs


def main(paths):
    files = [Path(p) for p in paths] or sorted(
        [p for p in (ROOT / "content").rglob("*.json") if p.name not in NON_QUESTION_FILES]
        + list((ROOT / "contracts" / "examples").glob("*.json"))
    )
    seen, failures, count = {}, 0, 0
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            print(f"{f}: top level must be a JSON array of questions")
            failures += 1
            continue
        for i, q in enumerate(data):
            count += 1
            shown = f.resolve().relative_to(ROOT) if f.resolve().is_relative_to(ROOT) else f
            label = f"{shown}[{i}] {q.get('id', '?')}"
            errs = [f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in VALIDATOR.iter_errors(q)]
            if not errs:
                errs = semantic_errors(q)
            qid = q.get("id")
            if qid in seen and "examples" not in str(f):
                errs.append(f"duplicate id (also in {seen[qid]})")
            seen[qid] = str(f)
            for e in errs:
                print(f"FAIL {label}: {e}")
            failures += bool(errs)
    print(f"{count} questions checked, {failures} failing")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
