"""Checkpoint invariants, original-content retention and independent algorithm checks."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import re

from pipeline import build, runner

ROOT = Path(__file__).resolve().parents[2]
EDITION = 'continuation-2026-11'


def questions():
    return [q for p in (ROOT / 'content').glob('*/*.json') if p.parent.name != 'demo'
            for q in json.loads(p.read_text(encoding='utf-8'))]


def originals():
    for name in build.corpus_names():
        source, cases = build.load(name)
        if getattr(cases, 'EDITION', None) == EDITION:
            ns = {}
            exec(source, ns)
            yield name, ns[cases.FUNCTION], cases


def test_checkpoints_add_twenty_at_a_time_and_retain_every_previous_question():
    bank = questions()
    ids = {q['id']: q for q in bank}
    assert len(ids) == len(bank)
    baseline = json.loads((Path(__file__).parent / 'fixtures/continuation-baseline.json').read_text())
    assert len(baseline) == 204
    for id_, digest in baseline.items():
        payload = {k: v for k, v in ids[id_].items() if k != 'placement'}
        assert hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest() == digest, id_
    added = [q for q in bank if EDITION in q.get('tags', [])]
    functions = list(originals())
    assert len(functions) % 2 == 0
    batches = len(functions) // 2
    assert 1 <= batches <= 5
    assert len(added) == batches * 20
    assert sum(q['track'] == 'debugging' for q in added) == batches * 10
    sd = [q for q in added if q['track'] == 'system-design']
    assert len(sd) == batches * 10
    for batch in range(1, batches + 1):
        assert sum(f'batch-{batch}' in q['tags'] for q in sd) == 10
    for q in sd:
        assert re.search(r'\[[^\]]+\]\(https://[^\s)]+\)', q['explanation']), q['id']
    assert len({q['prompt'] for q in sd}) == len(sd)


def test_every_continuation_mutant_fails_and_the_exact_repair_passes():
    new = [q for q in questions() if q['track'] == 'debugging' and EDITION in q.get('tags', [])]
    for name, _, cases in originals():
        qs = [q for q in new if q['provenance']['source_function'].endswith(f'/{name}.py::{cases.FUNCTION}')]
        assert len(qs) == 5, name
        source, _ = build.load(name)
        repairs = []
        for q in qs:
            lines = q['code'].split('\n')
            lines[q['answer'] - 1] = q['provenance']['original_line']
            fixed = '\n'.join(lines)
            assert fixed == source.rstrip('\n')
            repairs.append(fixed)
        broken = runner.run_many([q['code'] for q in qs], cases.FUNCTION, cases.CASES)
        fixed = runner.run_many(repairs, cases.FUNCTION, cases.CASES)
        for q, b, f in zip(qs, broken, fixed):
            assert b.status == 'fail', q['id']
            assert len(b.failed) == q['provenance']['tests_failed']
            assert f.status == 'pass', q['id']


def oracle(name, args):
    if name == 'running_max':
        xs, = args
        return [max(xs[:i + 1]) for i in range(len(xs))]
    if name == 'rotate_right':
        xs, k = args
        if not xs or not k % len(xs):
            return list(xs)
        shift = k % len(xs)
        return xs[-shift:] + xs[:-shift]
    if name == 'count_occurrences':
        xs, target = args
        return xs.count(target)
    if name == 'minimum_rotated':
        return min(args[0])
    raise AssertionError(f'Missing independent oracle: {name}')


def test_continuation_case_tables_have_independent_expected_values():
    for name, fn, cases in originals():
        assert len(cases.CASES) >= 8
        for args, expected in cases.CASES:
            assert expected == oracle(name, args), (name, args)
            copied = copy.deepcopy(args)
            assert fn(*copied) == expected
            assert copied == args, f'{name} mutated its input'


def test_array_functions_exhaustive_short_inputs():
    functions = {name: fn for name, fn, _ in originals()}
    for length in range(5):
        for values in itertools.product((-2, 0, 3), repeat=length):
            xs = list(values)
            assert functions['running_max'](xs) == oracle('running_max', (xs,))
            for k in range(8):
                assert functions['rotate_right'](xs, k) == oracle('rotate_right', (xs, k))


def test_binary_boundaries_and_rotated_minimum_exhaustive_short_inputs():
    functions = {name: fn for name, fn, _ in originals()}
    if 'count_occurrences' not in functions:
        return
    for length in range(6):
        for values in itertools.combinations_with_replacement((-2, 0, 3), length):
            xs = list(values)
            for target in range(-3, 5):
                assert functions['count_occurrences'](xs, target) == xs.count(target)
    for length in range(1, 6):
        for values in itertools.combinations(range(-3, 5), length):
            xs = list(values)
            for k in range(length):
                rotated = xs[k:] + xs[:k]
                assert functions['minimum_rotated'](rotated) == min(xs)
