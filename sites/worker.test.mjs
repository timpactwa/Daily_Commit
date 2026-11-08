import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { createWorker } from './worker.mjs';
import { MODULES } from './generated.mjs';

function database() {
  const db = new DatabaseSync(':memory:');
  db.exec(readFileSync(new URL('./drizzle/0000_learning_progress.sql', import.meta.url), 'utf8'));
  return { prepare(sql) { return { bind(...values) { return {
    async all() { return { results: db.prepare(sql).all(...values) }; },
    async run() { return db.prepare(sql).run(...values); },
  }; } }; }, close: () => db.close() };
}
function setup(upstreamFetch = async () => Response.json({ user_id: 'app-user' })) {
  const DB = database();
  const worker = createWorker({ upstreamFetch });
  const call = (path, body, siteUser = 'site-user') => worker.fetch(new Request(`https://example.test${path}`, {
    method: body === undefined ? 'GET' : 'POST', headers: { 'oai-authenticated-user-id': siteUser,
      'x-user-id': 'app-user', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body),
  }), { DB });
  return { DB, call, worker };
}

test('guides hide grading keys, enforce chapter order, and persist completion in SQL', async () => {
  const { call, DB } = setup();
  try {
    const m = MODULES[0], first = m.sections[0], second = m.sections[1];
    const publicView = await (await call(`/v1/learn/${m.topic}`)).json();
    assert.equal(publicView.sections.length, 4);
    assert.equal(publicView.sections[0].check.answer, undefined);
    assert.equal(publicView.sections[0].check.explanation, undefined);
    assert.equal((await call(`/v1/learn/${m.topic}/check`, { section_id: second.id, response: second.check.answer })).status, 409);
    const wrong = first.check.options.find(o => o.id !== first.check.answer).id;
    assert.equal((await (await call(`/v1/learn/${m.topic}/check`, { section_id: first.id, response: wrong })).json()).correct, false);
    assert.equal((await (await call(`/v1/learn/${m.topic}`)).json()).progress.passed.length, 0);
    for (const s of m.sections) {
      const r = await (await call(`/v1/learn/${m.topic}/check`, { section_id: s.id, response: s.check.answer })).json();
      assert.equal(r.correct, true);
      assert.equal(r.explanation, s.check.explanation);
    }
    assert.equal((await (await call(`/v1/learn/${m.topic}`)).json()).progress.completed, true);
    assert.equal((await (await call('/v1/learn')).json()).modules.find(x => x.topic === m.topic).passed, 4);
    assert.deepEqual((await (await call(`/v1/learn/${m.topic}`, undefined, 'different-visitor')).json()).progress.passed, []);
  } finally { DB.close(); }
});

test('private learning records require both Site identity and a verified app user', async () => {
  const { call, worker, DB } = setup(async () => Response.json({ error: { code: 'unknown_user' } }, { status: 401 }));
  try {
    assert.equal((await worker.fetch(new Request('https://example.test/v1/learn'), { DB })).status, 401);
    assert.equal((await call('/v1/learn')).status, 401);
  } finally { DB.close(); }
});

test('proxy forwards only app headers and maps existing ratings to seven numbered levels', async () => {
  let captured;
  const { worker, DB } = setup(async r => { captured = r; return Response.json({ topics: [999, 1000, 1350, 1400, 1650, 1900, 2100].map(rating => ({ rating })) }); });
  try {
    const response = await worker.fetch(new Request('https://example.test/v1/progress', { headers: {
      Authorization: 'Bearer app-session', 'x-user-id': 'app-user', 'x-client-date': '2026-11-08',
      'oai-authenticated-user-id': 'site-user', Cookie: 'platform-cookie', 'OAI-Sites-Authorization': 'private-service-token',
    } }), { DB });
    const data = await response.json();
    assert.deepEqual(data.topics.map(t => t.level), ['level-1','level-2','level-3','level-4','level-5','level-6','level-7']);
    assert.equal(data.skill_levels.length, 7);
    assert.equal(captured.url, 'https://daily-commit-production.up.railway.app/v1/progress');
    assert.equal(captured.headers.get('authorization'), 'Bearer app-session');
    for (const name of ['cookie', 'oai-authenticated-user-id', 'oai-sites-authorization']) assert.equal(captured.headers.get(name), null);
  } finally { DB.close(); }
});

test('all guides can be completed and reloaded without crossing visitor records', async () => {
  const { call, DB } = setup();
  try {
    for (const m of MODULES) {
      for (const s of m.sections) assert.equal((await call(`/v1/learn/${m.topic}/check`, { section_id: s.id, response: s.check.answer })).status, 200);
      assert.equal((await (await call(`/v1/learn/${m.topic}`)).json()).progress.completed, true);
    }
    assert.equal((await (await call('/v1/learn')).json()).modules.filter(m => m.completed).length, 10);
  } finally { DB.close(); }
});

test('Worker serves real built assets and does not fall back to HTML for missing scripts', async () => {
  const { worker, DB } = setup();
  try {
    const response = await worker.fetch(new Request('https://example.test/'), { DB });
    assert.match(await response.text(), /Daily Commit/);
    assert.match(response.headers.get('content-type'), /text\/html/);
    assert.equal((await worker.fetch(new Request('https://example.test/missing.js'), { DB })).status, 404);
  } finally { DB.close(); }
});
