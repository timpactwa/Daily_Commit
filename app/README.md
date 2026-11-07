# Daily Commit app

From `app/`, run `npm ci`, then `npm run dev -- --host`. Open the printed LAN URL on your phone; keep phone and laptop on the same Wi-Fi. The dev server proxies `/v1` to `http://127.0.0.1:8000`.

For standalone practice without the API, set `VITE_MOCK=1` before starting Vite (`$env:VITE_MOCK='1'` in PowerShell). Mock state lives in memory and resets on reload. The real API persists identity and answers. Clear `VITE_MOCK` for integration or production. Add `?demo=1` before the hash to request four-question placement from a demo-enabled server.

`npm run build` checks TypeScript and creates `dist/`, including the offline app shell. The API serves it at `/`. Hash routing lets all screens work through FastAPI's static-file mount. API calls are never cached by the service worker: offline mutations show retry rather than claiming an answer was saved.

`npm test` runs mobile and desktop browser flows. First run `npx playwright install chromium`; alternatively set `PLAYWRIGHT_CHANNEL=chrome` to use installed Chrome.

For a real API check, build the app, start the API with `DEMO_MODE=1` and `DB_PATH` pointing at a disposable file **outside `app/test-results/`**, then run `npx playwright test --config playwright.integration.config.ts` from `app/`. This resets the demo user on that server. The test verifies the production PWA and offline retry, and saves `app/test-results/home-phone.png`. It accepts the content bank currently loaded by the API.

Hold the logo for one second (pointer or keyboard) to switch to the demo user. The server must have `DEMO_MODE=1`. Install from the browser's app menu on Android/desktop, or Safari Share → Add to Home Screen on iOS. PWA installation and offline shell require HTTPS, or localhost.

## Deployment

The root `Dockerfile` builds the app and serves it through FastAPI in one service. On Railway, deploy from the repository root, attach a volume at `/data`, and set `DEMO_MODE=1` for the demo environment. `DB_PATH=/data/app.db` is set by the image. The service listens on Railway's `PORT` and uses `/health` for readiness. The public deployment is https://daily-commit-production.up.railway.app. Service settings are configured directly because Railway reports config-as-code settings updates deprecated; `railway.toml` also records the intended settings.

Local container check: `docker build -t daily-commit .`, then `docker run --rm -p 8000:8000 -v daily-commit-data:/data -e DEMO_MODE=1 daily-commit`. Run these from the repository root.

Backup tunnel on Windows: `./scripts/tunnel.ps1`; macOS/Linux: `bash scripts/tunnel.sh`. Requires Python dependencies, npm and cloudflared installed. The script builds the app, starts the API, checks health, prints a public HTTPS URL and stops the API on exit. Use `-SkipBuild` / `--skip-build` after a successful build. Windows can pass explicit executable paths using `-Python`, `-Npm`, `-Cloudflared`.

Before marking P4 complete: verify the public URL over cellular, answer a question, redeploy and confirm that user data survives. D2 tagging and feature freeze are a coordinated Tim + Liam task scheduled for Sunday at 10 AM; do not tag an unverified build.

Railway references: [Dockerfiles](https://docs.railway.com/builds/dockerfiles), [health checks](https://docs.railway.com/deployments/healthchecks), [volumes](https://docs.railway.com/volumes).

