"""Load /content into SQLite. Runs on every boot.

- Every question that passes contracts/validate.py checks is upserted.
- New questions start at their seed difficulty; existing ones keep their learned live rating.
- Questions no longer in /content are marked inactive (history stays intact).
- Invalid questions are skipped and logged, never fatal: one bad file must not take the demo down.
- If /content has no questions yet (early M1), contracts/examples is loaded so the API is usable.
- Questions under content/ranked/ go to the 'ranked' pool: never used by placement or lessons.
- Learning modules (content/learn/*.json) and the ranked manifest (content/ranked/tests.json)
  are validated and stored too. Invalid ones are skipped and logged.
"""
import json
import logging
import sqlite3
from pathlib import Path

from contracts.validate import VALIDATOR, is_question_file, is_ranked_file, learn_errors, ranked_errors, semantic_errors

log = logging.getLogger("content")
ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
EXAMPLES = ROOT / "contracts" / "examples"


def _read_questions(files: list[Path]) -> list[dict]:
    """Valid questions, each tagged with `_pool` ('lesson' | 'ranked') by file location."""
    out, seen = [], set()
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            log.error("skip %s: %s", f, e)
            continue
        if not isinstance(data, list):
            log.error("skip %s: top level must be an array", f)
            continue
        for q in data:
            errs = [e.message for e in VALIDATOR.iter_errors(q)] or semantic_errors(q)
            if errs:
                log.error("skip %s %s: %s", f.name, q.get("id", "?"), errs[0])
            elif q["id"] in seen:
                log.error("skip %s %s: duplicate id", f.name, q["id"])
            else:
                seen.add(q["id"])
                out.append({**q, "_pool": "ranked" if is_ranked_file(f) else "lesson"})
    return out


def find_question_files(content_dir: Path | None = None) -> list[Path]:
    content_dir = content_dir or CONTENT
    if not content_dir.is_dir():
        return []
    return sorted(p for p in content_dir.rglob("*.json") if is_question_file(p.relative_to(content_dir)))


def load(conn: sqlite3.Connection, content_dir: Path | None = None) -> int:
    content_dir = content_dir or CONTENT
    questions = _read_questions(find_question_files(content_dir))
    if not questions:
        log.warning("no questions in %s; loading contracts/examples", content_dir)
        questions = _read_questions(sorted(EXAMPLES.glob("*.json")))

    conn.execute("UPDATE questions SET active = 0")
    for q in questions:
        pool = q.pop("_pool")
        seed = float(q["difficulty_rating"])
        conn.execute(
            """INSERT INTO questions (id, track, topic, format, data, seed_rating, live_rating,
                                      source_function, placement, pool, active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
               ON CONFLICT(id) DO UPDATE SET
                 track = excluded.track, topic = excluded.topic, format = excluded.format,
                 data = excluded.data, seed_rating = excluded.seed_rating,
                 source_function = excluded.source_function, placement = excluded.placement,
                 pool = excluded.pool, active = 1""",
            (
                q["id"], q["track"], q["topic"], q["format"], json.dumps(q), seed, seed,
                (q.get("provenance") or {}).get("source_function"),
                1 if q.get("placement") and pool == "lesson" else 0, pool,
            ),
        )
    log.info("loaded %d questions", len(questions))
    load_learn(conn, content_dir)
    load_ranked(conn, content_dir, {q["id"]: q for q in questions if q["id"].split("-")[1:2] == ["ranked"]})
    return len(questions)


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        log.error("skip %s: %s", path, e)
        return None


def load_learn(conn: sqlite3.Connection, content_dir: Path) -> int:
    """Replace stored learning modules with the valid ones in content/learn, in topics.json order."""
    from api.repo import TOPIC_TRACK

    order = list(TOPIC_TRACK)
    conn.execute("DELETE FROM learn_modules")
    n = 0
    for path in sorted((content_dir / "learn").glob("*.json")) if (content_dir / "learn").is_dir() else []:
        m = _read_json(path)
        if m is None:
            continue
        errs = learn_errors(m, path.stem)
        if errs:
            log.error("skip learn/%s: %s", path.name, errs[0])
            continue
        conn.execute(
            "INSERT INTO learn_modules (topic, position, data) VALUES (?, ?, ?)",
            (m["topic"], order.index(m["topic"]), json.dumps(m)),
        )
        n += 1
    log.info("loaded %d learning modules", n)
    return n


def load_ranked(conn: sqlite3.Connection, content_dir: Path, ranked_questions: dict[str, dict]) -> int:
    """Store the ranked tiers if the manifest is valid. A bad manifest disables ranked tests (logged)."""
    conn.execute("DELETE FROM ranked_tiers")
    path = content_dir / "ranked" / "tests.json"
    if not path.is_file():
        return 0
    manifest = _read_json(path)
    if manifest is None:
        return 0
    errs = ranked_errors(manifest, ranked_questions)
    if errs:
        log.error("ranked tests disabled, content/ranked/tests.json: %s", errs[0])
        return 0
    for i, tier in enumerate(manifest["tiers"]):
        conn.execute("INSERT INTO ranked_tiers (id, position, data) VALUES (?, ?, ?)", (tier["id"], i, json.dumps(tier)))
    log.info("loaded %d ranked tiers", len(manifest["tiers"]))
    return len(manifest["tiers"])
