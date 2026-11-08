// Sites hosts the latest UI and guides; the existing API retains accounts and daily/ranked data.
import { ASSETS, MODULES, BANK } from './generated.mjs';
import { createPracticeHandler } from './practice.mjs';

const ORIGIN = 'https://daily-commit-production.up.railway.app';
const bands = [600, 1000, 1200, 1400, 1650, 1900, 2100];
const level = rating => Math.max(0, bands.findLastIndex(min => rating >= min));
const skill = rating => {
  const i = level(rating), next = bands[i + 1];
  return { level: `level-${i + 1}`, next_level: next ? `level-${i + 2}` : null,
    next_level_rating: next ?? null,
    level_progress: next ? Math.max(0, Math.min(100, Math.floor((rating - bands[i]) / (next - bands[i]) * 100))) : 100 };
};
const metadata = bands.map((min_rating, i) => ({ id: `level-${i + 1}`, min_rating, max_rating: (bands[i + 1] ?? 2201) - 1 }));
const rankedSuggestions = { beginner: ['Easy', 1, 3], intermediate: ['Intermediate', 4, 5], advanced: ['Advanced', 6, 7] };
const json = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store' } });
class ApiError extends Error {
  constructor(status, code, message) { super(message); this.status = status; this.code = code; }
}
const progress = (m, done) => {
  const passed = m.sections.map(s => s.id).filter(id => done.has(id));
  return { passed, sections: m.sections.length, completed: passed.length === m.sections.length };
};
const publicModule = (m, done) => ({ ...m, sections: m.sections.map(s => ({ ...s,
  check: { prompt: s.check.prompt, options: s.check.options } })), progress: progress(m, done) });

export function createWorker({ assets = ASSETS, modules = MODULES, bank = BANK, upstreamFetch = fetch } = {}) {
  async function upstream(request, path, method = request.method, body) {
    const headers = new Headers({ Accept: 'application/json' });
    // Never send the Site's identity, cookies, or platform service credentials to Railway.
    for (const name of ['authorization', 'x-user-id', 'x-client-date', 'content-type']) {
      const value = request.headers.get(name);
      if (value) headers.set(name, value);
    }
    const response = await upstreamFetch(new Request(ORIGIN + path, { method, headers,
      body: method === 'POST' ? body === undefined ? await request.arrayBuffer() : JSON.stringify(body) : undefined,
      redirect: 'manual', signal: AbortSignal.timeout(20000) }));
    // Workers supports manual/follow redirects. Block redirects explicitly so app
    // credentials and submitted answers can never be forwarded to another origin.
    if (response.status >= 300 && response.status < 400) {
      await response.body?.cancel();
      throw new ApiError(502, 'server', 'The API connection could not be completed. Please try again.');
    }
    return response;
  }
  async function identifyAppUser(request, env) {
    if (!request.headers.get('authorization') && !request.headers.get('x-user-id')) throw new ApiError(401, 'unknown_user', 'Start a practice profile or sign in first');
    const me = await upstream(request, '/v1/me', 'GET');
    const user = await me.json();
    if (!me.ok) throw new ApiError(me.status, user.error?.code ?? 'session_expired', user.error?.message ?? 'Sign in again');
    if (typeof user.user_id !== 'string') throw new ApiError(502, 'server', 'The profile could not be verified');
    const owner = JSON.stringify(['app', user.user_id]);
    const siteUser = request.headers.get('oai-authenticated-user-id');
    if (siteUser) {
      const legacy = JSON.stringify([siteUser, user.user_id]);
      const busy = await env.DB.prepare('SELECT 1 FROM sites_practice_sessions WHERE owner_id = ? AND locked_until > ? LIMIT 1').bind(legacy, Date.now()).all();
      if (busy.results.length) throw new ApiError(409, 'practice_busy', 'Your last answer is still saving. Try again.');
      // Preserve existing private-Site progress, then use the verified app session
      // for public visitors and signed-in visitors alike. Repeated imports never overwrite.
      await env.DB.prepare('INSERT OR IGNORE INTO sites_learning_progress (owner_id, topic, section_id) SELECT ?, topic, section_id FROM sites_learning_progress WHERE owner_id = ?').bind(owner, legacy).run();
      await env.DB.prepare('INSERT OR IGNORE INTO sites_practice_sessions (owner_id, lesson_id, day, data, completed) SELECT ?, lesson_id, day, data, completed FROM sites_practice_sessions WHERE owner_id = ?').bind(owner, legacy).run();
    }
    return owner;
  }
  const practice = createPracticeHandler({ upstream, bank, json, ApiError, identify: identifyAppUser });

  async function learn(request, env, path) {
    const owner = await identifyAppUser(request, env);
    const { results } = await env.DB.prepare('SELECT topic, section_id FROM sites_learning_progress WHERE owner_id = ?').bind(owner).all();
    const byTopic = new Map();
    for (const row of results) {
      if (!byTopic.has(row.topic)) byTopic.set(row.topic, new Set());
      byTopic.get(row.topic).add(row.section_id);
    }
    if (path === '/v1/learn' && request.method === 'GET') {
      return json({ modules: modules.map(m => {
        const p = progress(m, byTopic.get(m.topic) ?? new Set());
        return { topic: m.topic, track: m.track, title: m.title, summary: m.summary, minutes: m.minutes,
          sections: p.sections, passed: p.passed.length, completed: p.completed };
      }) });
    }
    const match = /^\/v1\/learn\/([a-z-]+)(\/check)?$/.exec(path);
    const m = modules.find(m => m.topic === match?.[1]);
    if (!m) throw new ApiError(404, 'not_found', 'Module not found');
    const done = byTopic.get(m.topic) ?? new Set();
    if (request.method === 'GET' && !match[2]) return json(publicModule(m, done));
    if (request.method !== 'POST' || !match[2]) throw new ApiError(405, 'invalid_response', 'Unsupported method');
    if (!request.headers.get('content-type')?.startsWith('application/json')) throw new ApiError(422, 'invalid_response', 'Expected JSON');
    const raw = await request.text();
    if (raw.length > 1024) throw new ApiError(413, 'invalid_response', 'Checkpoint request is too large');
    let body;
    try { body = JSON.parse(raw); } catch { throw new ApiError(422, 'invalid_response', 'Invalid JSON'); }
    if (!body || typeof body !== 'object') throw new ApiError(422, 'invalid_response', 'Invalid checkpoint');
    const index = m.sections.findIndex(s => s.id === body.section_id);
    if (index < 0) throw new ApiError(404, 'not_found', 'Section not found');
    const section = m.sections[index];
    if (!section.check.options.some(o => o.id === body.response)) throw new ApiError(422, 'invalid_response', 'Unknown option');
    if (m.sections.slice(0, index).some(s => !done.has(s.id))) throw new ApiError(409, 'locked', 'Finish the earlier sections first');
    const correct = section.check.answer === body.response;
    if (correct) {
      await env.DB.prepare('INSERT OR IGNORE INTO sites_learning_progress (owner_id, topic, section_id) VALUES (?, ?, ?)')
        .bind(owner, m.topic, section.id).run();
      done.add(section.id);
    }
    return json({ correct, ...progress(m, done), ...(correct ? { explanation: section.check.explanation } : {}) });
  }

  return {
    async fetch(request, env) {
      try {
        const url = new URL(request.url);
        let path;
        try { path = decodeURIComponent(url.pathname); } catch { throw new ApiError(400, 'invalid_response', 'Invalid request path'); }
        if (path.startsWith('/v1/') && /[?#%\\]/.test(path)) throw new ApiError(400, 'invalid_response', 'Invalid request path');
        if (path.startsWith('/v1/') && path.endsWith('/')) path = path.slice(0, -1);
        if (request.method !== 'GET' && request.method !== 'POST' && request.method !== 'HEAD') throw new ApiError(405, 'invalid_response', 'Unsupported method');
        if (path === '/v1/learn' || path.startsWith('/v1/learn/')) return await learn(request, env, path);
        if ((request.method === 'GET' && path === '/v1/lessons/today') || (request.method === 'POST' && (path === '/v1/answers' || /^\/v1\/lessons\/[^/]+\/(complete|retry)$/.test(path)))) return await practice(request, env, path);
        if (path.startsWith('/v1/') || path === '/health') {
          const response = await upstream(request, path + url.search);
          const data = await response.json();
          if (response.ok) {
            if (path === '/v1/demo/reset' || path === '/v1/demo/switch') {
              await env.DB.prepare('DELETE FROM sites_practice_sessions WHERE owner_id = ?').bind(JSON.stringify(['app', 'demo'])).run();
              const viewer = request.headers.get('oai-authenticated-user-id');
              if (viewer) await env.DB.prepare('DELETE FROM sites_practice_sessions WHERE owner_id = ?').bind(JSON.stringify([viewer, 'demo'])).run();
            }
            if (path === '/v1/progress') {
              data.skill_levels = metadata;
              data.topics = data.topics.map(t => ({ ...t, ...skill(t.rating) }));
            }
            if (path === '/v1/placement' && request.method === 'POST') data.topics = data.topics.map(t => ({ ...t, ...skill(t.rating) }));
            if (path === '/v1/config') data.features.learn = true;
            if (path.startsWith('/v1/ranked')) {
              const title = id => rankedSuggestions[id]?.[0];
              if (data.tier) data.title = title(data.tier) ?? data.title;
              if (data.tiers) {
                const p = await upstream(request, '/v1/progress', 'GET');
                const progress = await p.json();
                if (!p.ok) return json(progress, p.status);
                const average = progress.topics.length ? progress.topics.reduce((sum, t) => sum + t.rating, 0) / progress.topics.length : 600;
                data.ranked_level = level(average) + 1;
                data.ranked_rating = Math.floor(average);
                data.tiers = data.tiers.map(t => {
                  const [title, min_level, max_level] = rankedSuggestions[t.id];
                  return { ...t, title, min_level, max_level, suggested: min_level <= data.ranked_level && data.ranked_level <= max_level };
                });
              }
            }
          }
          return json(data, response.status);
        }
        if (request.method === 'POST') throw new ApiError(405, 'invalid_response', 'Unsupported method');
        const asset = assets[path] ?? (path === '/' || !path.split('/').pop().includes('.') ? assets['/index.html'] : null);
        if (!asset) return new Response('Not found', { status: 404 });
        const bytes = Uint8Array.from(atob(asset.data), c => c.charCodeAt(0));
        return new Response(request.method === 'HEAD' ? null : bytes, { headers: { 'Content-Type': asset.type,
          'Cache-Control': path.startsWith('/assets/') ? 'public, max-age=31536000, immutable' : 'no-cache',
          'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'strict-origin-when-cross-origin' } });
      } catch (error) {
        if (error instanceof ApiError) return json({ error: { code: error.code, message: error.message } }, error.status);
        console.error('Site request failed:', error.name, error.message);
        return json({ error: { code: 'server', message: 'The service is temporarily unavailable. Please try again.' } }, 502);
      }
    },
  };
}
export default createWorker();
