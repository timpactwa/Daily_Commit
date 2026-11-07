"""Load /content into SQLite. Runs on every boot.

- Every question that passes contracts/validate.py checks is upserted.
- New questions start at their seed difficulty; existing ones keep their learned live rating.
- Questions no longer in /content are marked inactive (history stays intact).
- Invalid questions are skipped and logged, never fatal: one bad file must not take the demo down.
- If /content has no questions yet (early M1), contracts/examples is loaded so the API is usable.
"""
import json
import logging
import sqlite3
from pathlib import Path

from contracts.validate import NON_QUESTION_FILES, VALIDATOR, semantic_errors

log = logging.getLogger("content")
ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
EXAMPLES = ROOT / "contracts" / "examples"


def _read_questions(files: list[Path]) -> list[dict]:
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
                out.append(q)
    return out


def find_question_files(content_dir: Path | None = None) -> list[Path]:
    content_dir = content_dir or CONTENT
    if not content_dir.is_dir():
        return []
    return sorted(p for p in content_dir.rglob("*.json") if p.name not in NON_QUESTION_FILES)


def load(conn: sqlite3.Connection, content_dir: Path | None = None) -> int:
    content_dir = content_dir or CONTENT
    questions = _read_questions(find_question_files(content_dir))
    if not questions:
        log.warning("no questions in %s; loading contracts/examples", content_dir)
        questions = _read_questions(sorted(EXAMPLES.glob("*.json")))

    conn.execute("UPDATE questions SET active = 0")
    for q in questions:
        seed = float(q["difficulty_rating"])
        conn.execute(
            """INSERT INTO questions (id, track, topic, format, data, seed_rating, live_rating,
                                      source_function, placement, active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
               ON CONFLICT(id) DO UPDATE SET
                 track = excluded.track, topic = excluded.topic, format = excluded.format,
                 data = excluded.data, seed_rating = excluded.seed_rating,
                 source_function = excluded.source_function, placement = excluded.placement,
                 active = 1""",
            (
                q["id"], q["track"], q["topic"], q["format"], json.dumps(q), seed, seed,
                (q.get("provenance") or {}).get("source_function"),
                1 if q.get("placement") else 0,
            ),
        )
    log.info("loaded %d questions", len(questions))
    return len(questions)
