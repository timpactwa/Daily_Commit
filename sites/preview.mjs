// Local-only portable preview. This file is never included in the production Worker.
import { createServer } from 'node:http';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { Readable } from 'node:stream';
import { createWorker } from './worker.mjs';

const db = new DatabaseSync(':memory:');
db.exec(readFileSync(new URL('./drizzle/0000_learning_progress.sql', import.meta.url), 'utf8'));
db.exec(readFileSync(new URL('./drizzle/0001_practice_mastery.sql', import.meta.url), 'utf8'));
const DB = { prepare(sql) { return { bind(...values) { return {
  async all() { return { results: db.prepare(sql).all(...values) }; },
  async run() { return db.prepare(sql).run(...values); },
}; } }; } };
const upstream = process.env.SITES_PREVIEW_API;
const worker = createWorker(upstream ? { upstreamFetch: request => {
  const url = new URL(request.url);
  return fetch(new Request(upstream + url.pathname + url.search, request));
} } : {});
const server = createServer(async (req, res) => {
  try {
    const headers = new Headers(req.headers);
    headers.set('oai-authenticated-user-id', 'local-preview-user');
    const request = new Request(`http://127.0.0.1:4174${req.url}`, { method: req.method, headers,
      ...(req.method === 'POST' ? { body: Readable.toWeb(req), duplex: 'half' } : {}) });
    const response = await worker.fetch(request, { DB });
    res.writeHead(response.status, Object.fromEntries(response.headers));
    res.end(Buffer.from(await response.arrayBuffer()));
  } catch { res.writeHead(500); res.end('Preview request failed'); }
});
server.listen(4174, '127.0.0.1', () => console.log('Local: http://127.0.0.1:4174'));
