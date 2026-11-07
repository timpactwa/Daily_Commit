# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS web
WORKDIR /build/app
COPY app/package.json app/package-lock.json ./
RUN npm ci
COPY app/src ./src
COPY app/public ./public
COPY app/scripts ./scripts
COPY app/index.html app/tsconfig.json app/vite.config.ts ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DB_PATH=/data/app.db
COPY api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY api ./api
COPY engine ./engine
COPY contracts ./contracts
# Content may not have landed yet during the early thin slice. The API has an
# examples fallback. Copy only content from the read-only source mount.
RUN --mount=type=bind,target=/source if [ -d /source/content ]; then cp -R /source/content /srv/content; else mkdir -p /srv/content; fi
COPY --from=web /build/app/dist ./app/dist
RUN mkdir -p /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/health',timeout=4)"
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
