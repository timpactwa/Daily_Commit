#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v cloudflared >/dev/null || { echo 'Install cloudflared first.' >&2; exit 1; }
python_bin="${PYTHON:-python3}"
if [[ -x .venv/bin/python ]]; then python_bin=.venv/bin/python; fi
if [[ "${1:-}" != "--skip-build" ]]; then
  (cd app && npm ci && npm run build)
fi
[[ -f app/dist/index.html ]] || { echo 'Build the app first.' >&2; exit 1; }
export DEMO_MODE=1
port="${PORT:-8000}"
"$python_bin" -m uvicorn api.main:app --host 127.0.0.1 --port "$port" &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
ready=0
for _ in {1..30}; do
  kill -0 "$server_pid" 2>/dev/null || { echo 'API exited before startup.' >&2; exit 1; }
  if curl -fsS "http://127.0.0.1:$port/health" >/dev/null; then ready=1; break; fi
  sleep 1
done
[[ "$ready" == 1 ]] || { echo 'API did not become healthy.' >&2; exit 1; }
echo 'Open the HTTPS URL below on your phone. Press Ctrl+C to stop.'
cloudflared tunnel --url "http://127.0.0.1:$port"
