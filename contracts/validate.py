"""Validate question content against the shared contracts.

Usage (from repo root):
    pip install jsonschema
    python contracts/validate.py                      # all content/**/*.json + contracts/examples
    python contracts/validate.py path/to/file.json    # specific files

Checks: JSON schema, topic id exists and matches track, unique ids,
answer refers to a real option/node/line, reorder answer is a permutation.
Also checks learning modules (content/learn/*.json, learn.schema.json) and the ranked
test manifest (content/ranked/tests.json, ranked.schema.json).
Exit code 1 on any error. CI runs this on every PR.
"""
import ast
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "contracts" / "question.schema.json").read_text(encoding="utf-8"))
TOPICS = {t["id"]: t["track"] for t in json.loads((ROOT / "contracts" / "topics.json").read_text(encoding="utf-8"))["topics"]}
VALIDATOR = Draft202012Validator(SCHEMA)
LEARN_VALIDATOR = Draft202012Validator(json.loads((ROOT / "contracts" / "learn.schema.json").read_text(encoding="utf-8")))
RANKED_VALIDATOR = Draft202012Validator(json.loads((ROOT / "contracts" / "ranked.schema.json").read_text(encoding="utf-8")))
NON_QUESTION_FILES = {"showcase.json", "demo-user.json", "tests.json"}
NON_QUESTION_DIRS = {"learn"}
RANKED_DIR = "ranked"


def is_question_file(p: Path) -> bool:
    return p.name not in NON_QUESTION_FILES and not (set(p.parts) & NON_QUESTION_DIRS)


def is_ranked_file(p: Path) -> bool:
    return RANKED_DIR in p.parts


def learn_errors(m, stem: str | None = None):
    """Learning module checks beyond the schema."""
    errs = [f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in LEARN_VALIDATOR.iter_errors(m)]
    if errs:
        return errs
    if TOPICS.get(m["topic"]) != m["track"]:
        errs.append(f"topic '{m['topic']}' unknown or not in track '{m['track']}'")
    if stem is not None and stem != m["topic"]:
        errs.append(f"file name '{stem}' must equal topic '{m['topic']}'")
    ids = [s["id"] for s in m["sections"]]
    if len(ids) != len(set(ids)):
        errs.append("duplicate section ids")
    for s in m["sections"]:
        opts = [o["id"] for o in s["check"]["options"]]
        if len(opts) != len(set(opts)):
            errs.append(f"section {s['id']}: duplicate option ids")
        if s["check"]["answer"] not in opts:
            errs.append(f"section {s['id']}: answer '{s['check']['answer']}' is not an option id")
        if m["track"] == "debugging" and "code" in s["example"]:
            try:
                ast.parse(s["example"]["code"])
            except SyntaxError as e:
                errs.append(f"section {s['id']}: example code does not parse ({e.msg})")
    return errs


def ranked_errors(manifest, questions: dict[str, dict]):
    """Manifest checks: schema, every id exists under content/ranked, difficulty within the tier band, 5+5 split."""
    errs = [f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in RANKED_VALIDATOR.iter_errors(manifest)]
    if errs:
        return errs
    if [t["id"] for t in manifest["tiers"]] != ["beginner", "intermediate", "advanced"]:
        errs.append("tiers must be beginner, intermediate, advanced in that order")
    used = set()
    for t in manifest["tiers"]:
        tracks = {"system-design": 0, "debugging": 0}
        missing = False
        for qid in t["questions"]:
            if qid in used:
                errs.append(f"{t['id']}: {qid} is used in more than one tier")
            used.add(qid)
            q = questions.get(qid)
            if q is None:
                errs.append(f"{t['id']}: {qid} not found in content/ranked")
                missing = True
                continue
            tracks[q["track"]] += 1
            if not t["min_rating"] <= q["difficulty_rating"] < t["max_rating"]:
                errs.append(f"{t['id']}: {qid} difficulty {q['difficulty_rating']} outside [{t['min_rating']}, {t['max_rating']})")
        if not missing and tracks != {"system-design": 5, "debugging": 5}:
            errs.append(f"{t['id']}: needs 5 system-design + 5 debugging, has {tracks}")
    return errs


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
    content = ROOT / "content"
    all_json = sorted(content.rglob("*.json")) if content.is_dir() else []
    files = [Path(p) for p in paths] or sorted(
        [p for p in all_json if is_question_file(p)] + list((ROOT / "contracts" / "examples").glob("*.json"))
    )
    seen, failures, count = {}, 0, 0
    ranked_questions: dict[str, dict] = {}
    for f in files:
        if not is_question_file(f):
            continue
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
            is_ranked_id = isinstance(qid, str) and qid.split("-", 2)[1:2] == ["ranked"]
            if is_ranked_file(f) != is_ranked_id:
                errs.append("ranked questions (id sd-ranked-* / dbg-ranked-*) must live in content/ranked/, and only there")
            if is_ranked_file(f) and not errs:
                ranked_questions[qid] = q
            if qid in seen and "examples" not in str(f):
                errs.append(f"duplicate id (also in {seen[qid]})")
            seen[qid] = str(f)
            for e in errs:
                print(f"FAIL {label}: {e}")
            failures += bool(errs)
    print(f"{count} questions checked, {failures} failing")

    if not paths:
        modules = [p for p in all_json if "learn" in p.parts]
        bad = 0
        for p in modules:
            for e in learn_errors(json.loads(p.read_text(encoding="utf-8")), p.stem):
                print(f"FAIL {p.relative_to(ROOT)}: {e}")
                bad += 1
        print(f"{len(modules)} learning modules checked, {bad} errors")
        failures += bad
        manifest = content / RANKED_DIR / "tests.json"
        if manifest.is_file():
            errs = ranked_errors(json.loads(manifest.read_text(encoding="utf-8")), ranked_questions)
            for e in errs:
                print(f"FAIL content/ranked/tests.json: {e}")
            print(f"ranked manifest checked, {len(errs)} errors")
            failures += len(errs)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
