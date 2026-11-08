// Sites hosts the latest UI and guides; the existing API retains accounts and daily/ranked data.
import { ASSETS, MODULES } from './generated.mjs';

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

export function createWorker({ assets = ASSETS, modules = MODULES, upstreamFetch = fetch } = {}) {
  async function upstream(request, path, method = request.method) {
    const headers = new Headers({ Accept: 'application/json' });
    // Never send the Site's identity, cookies, or platform service credentials to Railway.
    for (const name of ['authorization', 'x-user-id', 'x-client-date', 'content-type']) {
      const value = request.headers.get(name);
      if (value) headers.set(name, value);
    }
    const response = await upstreamFetch(new Request(ORIGIN + path, { method, headers,
      body: method === 'POST' ? await request.arrayBuffer() : undefined,
      redirect: 'manual', signal: AbortSignal.timeout(20000) }));
    // Workers supports manual/follow redirects. Block redirects explicitly so app
    // credentials and submitted answers can never be forwarded to another origin.
    if (response.status >= 300 && response.status < 400) {
      await response.body?.cancel();
      throw new ApiError(502, 'server', 'The API connection could not be completed. Please try again.');
    }
    return response;
  }

  async function learn(request, env, path) {
    const siteUser = request.headers.get('oai-authenticated-user-id');
    if (!siteUser) throw new ApiError(401, 'session_expired', 'Sign in to this Site to save your learning progress.');
    const me = await upstream(request, '/v1/me', 'GET');
    if (!me.ok) return new Response(me.body, { status: me.status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
    const user = await me.json();
    const owner = JSON.stringify([siteUser, user.user_id]);
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
        const url = new URL(request.url), path = url.pathname;
        if (request.method !== 'GET' && request.method !== 'POST' && request.method !== 'HEAD') throw new ApiError(405, 'invalid_response', 'Unsupported method');
        if (path === '/v1/learn' || path.startsWith('/v1/learn/')) return await learn(request, env, path);
        if (path.startsWith('/v1/') || path === '/health') {
          const response = await upstream(request, path + url.search);
          const data = await response.json();
          if (response.ok) {
            if (path === '/v1/progress') {
              data.skill_levels = metadata;
              data.topics = data.topics.map(t => ({ ...t, ...skill(t.rating) }));
            }
            if (path === '/v1/placement' && request.method === 'POST') data.topics = data.topics.map(t => ({ ...t, ...skill(t.rating) }));
            if (path === '/v1/config') data.features.learn = true;
            if (path.startsWith('/v1/ranked')) {
              const title = id => ({ beginner: 'Level 1', intermediate: 'Level 3', advanced: 'Level 5' })[id];
              if (data.tier) data.title = title(data.tier) ?? data.title;
              if (data.tiers) {
                const p = await upstream(request, '/v1/progress', 'GET');
                let suggested;
                if (p.ok) {
                  const topics = (await p.json()).topics;
                  const mean = topics.reduce((sum, t) => sum + t.rating, 0) / topics.length;
                  suggested = mean < 1200 ? 'beginner' : mean < 1650 ? 'intermediate' : 'advanced';
                }
                data.tiers = data.tiers.map(t => ({ ...t, title: title(t.id) ?? t.title, ...(suggested ? { suggested: t.id === suggested } : {}) }));
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
