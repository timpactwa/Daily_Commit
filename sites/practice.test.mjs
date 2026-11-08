import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { createWorker } from './worker.mjs';
import { practiceAttemptLimit } from './practice.mjs';

const options = ['a','b','c','d'].map(id => ({ id, text: id.toUpperCase() }));
const qs = [
  { id: 'mcq', format: 'mcq', options, answer: 'b' },
  { id: 'binary', format: 'mcq', options: options.slice(0,2), answer: 'b' },
  { id: 'code', format: 'tap_line', code: 'def f(x):\n    return x - 1\n# end', answer: 2 },
  { id: 'order', format: 'reorder', options: options.slice(0,3), answer: ['a','b','c'] },
  { id: 'nodes', format: 'tap_node', options: options.slice(0,3), answer: 'b' },
  { id: 'output', format: 'predict_output', options: options.slice(0,3), code: 'print(2)', answer: 'b' },
].map(q => ({ ...q, topic: 'caching', difficulty_rating: 1200, explanation: 'The concept explains the correct answer.' }));

function fixture(completed = false) {
  const db = new DatabaseSync(':memory:');
  for (const file of ['0000_learning_progress.sql','0001_practice_mastery.sql']) db.exec(readFileSync(new URL(`./drizzle/${file}`, import.meta.url), 'utf8'));
  const DB = { prepare(sql) { return { bind(...args) { return {
    async all() { return { results: db.prepare(sql).all(...args) }; }, async run() { return db.prepare(sql).run(...args); },
  }; } }; } };
  const calls = { answers: 0, completes: 0 };
  let day = '2026-11-08';
  const answered = new Set();
  const worker = createWorker({ bank: Object.fromEntries(qs.map(q => [q.id,q])), upstreamFetch: async request => {
    const path = new URL(request.url).pathname;
    if (path === '/v1/me') return Response.json({ user_id: request.headers.get('x-user-id') });
    if (path === '/v1/lessons/today') return Response.json({ lesson_id: `lesson_${day}`, date: day, status: completed ? 'completed' : 'in_progress', focus_topics: ['caching'], items: qs.map((q,i) => ({ position: i+1, kind: 'focus', answered: completed, correct: completed ? false : null, question: Object.fromEntries(Object.entries(q).filter(([k]) => !['answer','explanation'].includes(k))) })) });
    if (path === '/v1/answers') {
      const body = await request.json(), q = qs.find(q => q.id === body.question_id);
      assert(!answered.has(q.id), 'Elo was requested more than once for a question');
      answered.add(q.id); calls.answers++;
      await new Promise(resolve => setTimeout(resolve, 3));
      const correct = JSON.stringify(body.response) === JSON.stringify(q.answer);
      return Response.json({ correct, score: correct ? 1 : 0, correct_answer: q.answer, explanation: q.explanation,
        rating: { topic: q.topic, before: 1200, after: correct ? 1210 : 1190, delta: correct ? 10 : -10 }, question_rating: { before: 1200, after: 1200 } });
    }
    if (path === '/v1/progress') return Response.json({ topics: [{ topic: 'caching', rating: 1200 }] });
    if (path.endsWith('/complete')) { calls.completes++; return Response.json({ summary: { correct: 0, total: 6 }, rating_changes: [], streak: { current: 1, best: 1, today_done: true, extended: true } }); }
    throw new Error(`Unexpected upstream route ${path}`);
  } });
  const call = (path, body, user = 'alice') => worker.fetch(new Request(`https://example.test${path}`, { method: body === undefined ? 'GET' : 'POST', headers: { 'x-user-id': user, 'oai-authenticated-user-id': 'site-viewer', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) }), { DB });
  const answer = (id, response) => call('/v1/answers', { lesson_id: 'lesson_2026-11-08', question_id: id, response, time_ms: 100 });
  return { call, answer, calls, nextDay: () => { day = '2026-11-09'; }, close: () => db.close() };
}

test('attempt limits depend on the question type and number of choices', () => {
  assert.deepEqual(qs.map(practiceAttemptLimit), [2,1,2,1,2,2]);
});

test('four of six within the allowed tries passes; retry feedback never reveals the answer', async () => {
  const f = fixture();
  try {
    assert.equal((await (await f.call('/v1/lessons/today')).json()).mastery.required, 4);
    const first = await (await f.answer('mcq','a')).json();
    assert.deepEqual(Object.keys(first).sort(), ['attempt_limit','attempts_used','correct','lesson_progress','retry_available']);
    assert.equal(first.retry_available, true);
    const repeated = await (await f.answer('mcq','a')).json();
    assert.equal(repeated.attempts_used, 1); assert.equal(f.calls.answers, 1);
    const saved = await (await f.call('/v1/lessons/today')).json();
    assert.equal(saved.items[0].answered, false); assert.equal(saved.items[0].attempts_used, 1);
    const second = await (await f.answer('mcq','b')).json();
    assert.equal(second.correct, true); assert.equal(second.rating.delta, 0);
    assert.equal((await (await f.answer('binary','a')).json()).retry_available, false);
    await f.answer('code',1); await f.answer('code',3);
    await f.answer('order',['a','b','c']); await f.answer('nodes','a'); await f.answer('nodes','b'); await f.answer('output','b');
    const view = await (await f.call('/v1/lessons/today')).json();
    assert.equal(view.mastery.correct, 4); assert.equal(view.mastery.can_complete, true);
    const done = await (await f.call('/v1/lessons/lesson_2026-11-08/complete',{})).json();
    assert.deepEqual(done.summary, { correct: 4, total: 6 });
    await f.call('/v1/lessons/lesson_2026-11-08/complete',{});
    assert.equal(f.calls.completes, 1); assert.equal(f.calls.answers, 6);
  } finally { f.close(); }
});

test('three of six blocks finishing and next-day advancement; a full retry does not farm Elo', async () => {
  const f = fixture();
  try {
    await f.call('/v1/lessons/today');
    await f.answer('mcq','b'); await f.answer('binary','b'); await f.answer('code',2);
    await f.answer('order',['c','b','a']); await f.answer('nodes','a'); await f.answer('nodes','c'); await f.answer('output','a'); await f.answer('output','c');
    assert.equal((await f.call('/v1/lessons/lesson_2026-11-08/complete',{})).status, 409);
    assert.equal(f.calls.completes, 0);
    f.nextDay();
    assert.equal((await (await f.call('/v1/lessons/today')).json()).date, '2026-11-08');
    const retry = await (await f.call('/v1/lessons/lesson_2026-11-08/retry',{})).json();
    assert.equal(retry.mastery.round, 2); assert.equal(retry.mastery.correct, 0);
    for (const q of qs) assert.equal((await f.answer(q.id,q.answer)).status, 200);
    assert.equal(f.calls.answers, 6);
    assert.equal((await f.call('/v1/lessons/lesson_2026-11-08/complete',{})).status, 200);
    assert.equal((await (await f.call('/v1/lessons/today')).json()).date, '2026-11-09');
  } finally { f.close(); }
});

test('partial lessons, other users, invalid answers, and encoded completion paths cannot bypass the gate', async () => {
  const f = fixture();
  try {
    await f.call('/v1/lessons/today');
    assert.equal((await f.call('/v1/lessons/lesson_2026-11-08/complete',{})).status,409);
    assert.equal((await f.call('/v1/lessons/lesson%5F2026-11-08/complete',{})).status,409);
    assert.equal((await f.call('/v1/%256cessons/lesson_2026-11-08/complete',{})).status,400);
    assert.equal((await f.call('/v1/lessons/lesson_2026-11-08/complete',{},'bob')).status,404);
    assert.equal((await f.answer('code',999)).status,422);
    assert.equal((await f.answer('order',['a','a','b'])).status,422);
    assert.equal((await f.call('/v1/lessons/lesson_2026-11-08/retry',{})).status,409);
    assert.equal(f.calls.answers,0); assert.equal(f.calls.completes,0);
  } finally { f.close(); }
});

test('concurrent submissions serialize and cannot duplicate the Elo update', async () => {
  const f = fixture();
  try {
    await f.call('/v1/lessons/today');
    const responses = await Promise.all([f.answer('mcq','a'),f.answer('mcq','b')]);
    assert.deepEqual(responses.map(r => r.status).sort(),[200,409]);
    assert.equal(f.calls.answers,1);
  } finally { f.close(); }
});

test('previously completed lessons stay complete without awarding another streak', async () => {
  const f = fixture(true);
  try {
    assert.equal((await (await f.call('/v1/lessons/today')).json()).status, 'completed');
    const result = await (await f.call('/v1/lessons/lesson_2026-11-08/complete',{})).json();
    assert.equal(result.streak.extended, false);
    assert.equal(f.calls.completes, 0);
  } finally { f.close(); }
});
