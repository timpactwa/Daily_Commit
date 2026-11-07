"""Editorial and independent execution checks for the November research edition."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from pipeline import build, runner

ROOT = Path(__file__).resolve().parents[2]
EDITION = "research-2026-11"
TOPICS = {"arrays-strings", "binary-search", "recursion", "sorting", "hash-maps"}


def edition_debugging():
    return [q for q in json.loads(build.OUT.read_text(encoding="utf-8")) if EDITION in q.get("tags", [])]


def test_research_edition_adds_fifty_debugging_questions_from_fifteen_functions():
    questions = edition_debugging()
    assert len(questions) == 50
    assert Counter(q["topic"] for q in questions) == {topic: 10 for topic in TOPICS}
    assert len({q["provenance"]["source_function"] for q in questions}) == 15
    for q in questions:
        name = Path(q["provenance"]["source_function"].split("::")[0]).stem
        _, cases = build.load(name)
        assert cases.EDITION == EDITION
        assert len(cases.CASES) >= 8


def test_every_added_mutant_fails_and_repairing_its_answer_line_passes():
    groups = defaultdict(list)
    for q in edition_debugging():
        name = Path(q["provenance"]["source_function"].split("::")[0]).stem
        groups[name].append(q)
    for name, questions in groups.items():
        original, cases = build.load(name)
        repairs = []
        for q in questions:
            lines = q["code"].split("\n")
            lines[q["answer"] - 1] = q["provenance"]["original_line"]
            fixed = "\n".join(lines)
            assert fixed == original.rstrip("\n"), q["id"]
            repairs.append(fixed)
        broken_results = runner.run_many([q["code"] for q in questions], cases.FUNCTION, cases.CASES)
        repaired_results = runner.run_many(repairs, cases.FUNCTION, cases.CASES)
        for q, broken, repaired in zip(questions, broken_results, repaired_results):
            assert broken.status == "fail", q["id"]
            assert repaired.status == "pass", q["id"]
            assert len(broken.failed) == q["provenance"]["tests_failed"]
            assert broken.total == q["provenance"]["tests_total"]


def test_research_system_design_questions_have_primary_source_citations():
    questions = []
    for file in (ROOT / "content/system-design").glob("*.json"):
        questions.extend(q for q in json.loads(file.read_text(encoding="utf-8")) if EDITION in q.get("tags", []))
    assert len(questions) == 50
    assert set(Counter(q["topic"] for q in questions).values()) == {10}
    allowed_hosts = {"www.rfc-editor.org", "redis.io", "docs.aws.amazon.com", "learn.microsoft.com", "docs.memcached.org", "kubernetes.io", "grpc.io", "docs.nginx.com", "www.postgresql.org", "kafka.apache.org", "www.rabbitmq.com", "sre.google", "aws.amazon.com"}
    sources = set()
    for q in questions:
        citations = re.findall(r"\[[^\]]+\]\((https://[^\s)]+)\)", q["explanation"])
        assert citations, q["id"]
        for citation in citations:
            assert urlparse(citation).hostname in allowed_hosts, (q["id"], citation)
            sources.add(citation)
    assert len(sources) >= 30
