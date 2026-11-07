# Liam's implementation handoff

Public app: https://daily-commit-production.up.railway.app
Railway project: https://railway.com/project/0d5c44e1-13ef-49af-b7d7-89873ddec369

## Tasks

| Task | PR | Result |
| --- | --- | --- |
| S3 CI | #50 | Merged; GitHub Actions is active |
| S4 Shell | #51 | Merged |
| T3 Lesson player | #52 | Merged |
| C3 Placement | #53 | Merged |
| C4 Reorder | #54 | Merged |
| C10 TapNode | #55 | Merged |
| P5 Dashboard and progress | #56 | Merged |
| P7 Mobile PWA | #57 | Merged |
| P4 Deployment | #58 | Public cloud deployment and mobile-browser checks passed; final merge/redeploy and physical-phone confirmation finish the task |
| D2 Freeze | Issue #37 | Tim + Liam coordinate Sunday Nov 8, 10 AM ET, after M3; tag only the verified demo build |

Each implementation task has its own PR. The first eight task issues closed through their merged PRs. Keep #28 open until deployment persistence and the physical cellular check are confirmed.

## Verification

- Every task branch builds with npm.
- GitHub CI passes the question validator, API/engine/pipeline tests, frontend build, six phone/desktop mock browser flows, and the production container build/startup check.
- The public Railway API loaded 104 questions from both tracks. Fresh-user placement returns ten questions; a normal daily lesson contains six items and both tracks.
- The production PWA test passed against public HTTPS: demo switching, server grading, Elo feedback, lesson completion, progress, offline shell reload and retry after reconnecting.
- A separate non-demo deployment-check user has completed placement and answered a lesson question. Its ratings/history/answer baseline is saved outside the repository in `.tools/railway-persistence.json` for comparison after redeploy. Demo data intentionally resets on every boot and must not be used to prove persistence.
- Production mock answer fixtures are excluded unless mock mode is explicitly enabled.
- PowerShell tunnel script and Railway TOML parse. The production image was built and started both in GitHub Actions and Railway. The simplified Dockerfile copies committed content directly; the earlier source-bind recipe was rejected by Railway's pre-build validator.
- Physical cellular access and Add to Home Screen need the user's device confirmation; browser emulation does not prove those checks.

## Deployment

Service `daily-commit` runs FastAPI and serves `app/dist` on port 8000, with `/health` readiness, demo mode enabled and SQLite at `/data/app.db`. The persistent `/data` volume is 500 MB. Railway service settings explicitly configure the Dockerfile, healthcheck and restart policy. The legacy `railway.toml` remains a repository reference; the connected tool reports config-as-code settings updates deprecated, so service settings are applied directly.

Production environment: `48ffc7e6-a4b9-4c95-aca8-f30693da7a7e`.
Service: `4efa730e-24f4-4838-8a62-019036a81346`.
Volume: `9684274c-06e9-42a9-b555-d16696c058f0`.

The user authorized GitHub publication and Railway repository access/deployment. Initial deployment verification uses a CI-verified PR commit. After #58 merges, connect the service to `timpactwa/Daily_Commit@main` without a commit pin for automatic deployments, and compare the non-demo user's state after that deployment settles.

The current GitHub account has push access but no repository administration access. Tim should ensure the CI check names are required by main's branch protection; the agent only merged application PRs after their checks passed. The CI-only bootstrap merge was explicitly authorized by Liam when GitHub initially reported zero workflows.

## Local worktrees and commands

The main checkout is `Daily_Commit`; publication worktree is `../project-worktrees/app-publish`. Task branches are named `app-s3`, `app-s4`, `app-t3`, `app-c3`, `app-c4`, `app-c10`, `app-p5`, `app-p7`, `app-p4`. The earlier combined implementation remains on local branch `app` in `../project-worktrees/app`.

See [README.md](README.md) for development, mock mode, real API, phone and tunnel commands. All authored changes stay in Liam's owned paths. Shared contracts, backend, pipeline and `app/src/api` were only brought in through main merges.

The integration test resets the demo user on its target server. Use an isolated local database outside `app/test-results`, or explicitly target the demo environment with `DAILY_COMMIT_TEST_URL`. Keep `VITE_MOCK` unset for production.
