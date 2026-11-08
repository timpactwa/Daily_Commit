import { readFile, readdir, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

// Run from the repository root after building app/. Outputs one portable Worker ESM.
const root = process.cwd();
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.webmanifest': 'application/manifest+json',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.woff2': 'font/woff2' };
const assets = {};
async function collect(directory, prefix = '') {
  for (const item of await readdir(directory, { withFileTypes: true })) {
    const name = path.join(directory, item.name), url = `${prefix}/${item.name}`;
    if (item.isDirectory()) await collect(name, url);
    else assets[url] = { type: types[path.extname(item.name)] ?? 'application/octet-stream', data: (await readFile(name)).toString('base64') };
  }
}
await collect(path.join(root, 'app/dist'));
if (!assets['/index.html']) throw new Error('Build app/ before packaging the Site');
const files = (await readdir(path.join(root, 'content/learn'))).filter(f => f.endsWith('.json')).sort();
const modules = await Promise.all(files.map(async f => JSON.parse(await readFile(path.join(root, 'content/learn', f), 'utf8'))));
const generated = `export const ASSETS = ${JSON.stringify(assets)};\nexport const MODULES = ${JSON.stringify(modules)};\n`;
await writeFile(path.join(root, 'sites/generated.mjs'), generated);
const source = await readFile(path.join(root, 'sites/worker.mjs'), 'utf8');
await mkdir(path.join(root, 'dist/server'), { recursive: true });
await writeFile(path.join(root, 'dist/server/index.js'), source.replace("import { ASSETS, MODULES } from './generated.mjs';", generated.replaceAll('export const', 'const')));
await mkdir(path.join(root, 'dist/.openai'), { recursive: true });
try {
  await writeFile(path.join(root, 'dist/.openai/hosting.json'), await readFile(path.join(root, '.openai/hosting.json')));
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
  // The GitHub checkout has no Site identity; only the dedicated Site checkout does.
}
console.log(`Built Sites Worker: ${Object.keys(assets).length} assets, ${modules.length} guides`);
