# Liam's implementation handoff

Worktree: `../project-worktrees/app`. Integration branch: `app`.
Latest backend main was merged before integration verification. All authored changes are in Liam's owned paths; `app/src/api/`, contracts, backend and other owners' files were not edited.

## Task status

| Task | GitHub issue | Local result | Still required |
| --- | --- | --- | --- |
| S3 CI | #3 | Validator, Python module tests, frontend build, phone/desktop browser jobs | Publish PR; confirm green checks and set required checks on main |
| S4 App shell | #4 | Vite, React, TypeScript, Tailwind, hash routes and LAN dev server | Publish PR; physical phone LAN check |
| T3 Lesson player | #11 | MCQ, code-line selection, feedback, Elo deltas, answer timing, resume/retry | Publish PR |
| C3 Placement | #17 | Dynamic question count, progress, single final submission, grouped results | Publish PR; full 10-question bank when content lands |
| C4 Reorder | #18 | Tap to order, remove, reset; complete ID array required | Publish PR |
| C10 TapNode | #24 | Scrollable left-to-right diagram, selectable nodes, option-list fallback | Publish PR |
| P5 Screens | #29 | Home, streak, completion, readiness, history sparklines, tomorrow preview | Publish PR |
| P7 Mobile | #31 | Loading, retry, haptics, safe areas, PWA, long-press demo switch | Publish PR; physical Add to Home Screen check |
| P4 Deploy | #28 | Dockerfile, Railway config, tunnel scripts; Railway project and staged service, demo variables, 500 MB /data volume | Approve repo connection and deployment, Docker/cloud build, public HTTPS and cellular check, persistence across redeploy |
| D2 Freeze | #37 | Not started | Tim + Liam coordinate Sunday Nov 8, 10 AM ET after M3; tag only verified demo build |

The GitHub issues remain open: repository rules close each task through its merged PR. Do not close deployment or device checks on the basis of emulation alone.

## Verification

- `npm run build` passes, including TypeScript and PWA shell generation.
- Six Playwright mock flows pass across Pixel 7 emulation and desktop: placement, all four formats, feedback, completion, progress, reorder undo and six-to-seven streak.
- One production PWA test passes against the real FastAPI server: demo switching, server grading, Elo feedback, lesson completion, progress, offline shell reload and retry after reconnecting.
- `pytest api engine`: 79 passed. Pipeline has not landed in the checked main; CI includes it as soon as that directory exists.
- `python contracts/validate.py`: four contract-example questions, zero failures. The current checkout has no content bank yet; API fallback examples were used.
- Production JS was checked for contract-example question IDs/text; mock answer fixtures are excluded by the Vite resolver unless mock mode is explicitly enabled.
- Railway TOML and PowerShell tunnel script parse successfully. Docker executable is present but its Linux daemon is stopped. No container or public deployment has been claimed as tested.

## Publishing plan

Keep one task per PR, with titles starting with task IDs and the corresponding closing reference. Commits on `app` are task-labelled; prepare task branches and verify each against latest main before publishing. CI and shell are a bootstrap dependency: land the shell before requiring the frontend build. Include browser tests once the completed mobile flow is available.

Suggested PR titles and closing lines:

| Title | Body closing line |
| --- | --- |
| S3 app: validate questions, test Python and build frontend in CI | Closes #3 |
| S4 app: add mobile React shell and routes | Closes #4 |
| T3 app: add lesson player and graded feedback | Closes #11 |
| C3 app: add placement and topic-level results | Closes #17 |
| C4 app: add tap-to-order questions | Closes #18 |
| C10 app: add selectable diagrams with option fallback | Closes #24 |
| P5 app: show daily practice, streaks and progress | Closes #29 |
| P7 app: add PWA installation, offline retry and demo switching | Closes #31 |

For P4, use a draft PR until public URL, volume and phone verification pass; include the deployment URL and persistence evidence before closing #28.

Publishing is awaiting explicit authorization after automatic approval review rejected saved-account enumeration. Do not work around that rejection with another credential source.

Railway is connected. Project [Daily Commit](https://railway.com/project/0d5c44e1-13ef-49af-b7d7-89873ddec369), production environment `48ffc7e6-a4b9-4c95-aca8-f30693da7a7e`, has six staged changes in patch `5049f0ac-9ca2-49c4-83c2-cf1fb44fd98f`: empty `daily-commit` service, `DEMO_MODE=1`, `DB_PATH=/data/app.db`, and a 500 MB volume at `/data`. None is deployed or provisioned yet. Service ID: `4efa730e-24f4-4838-8a62-019036a81346`; volume ID: `9684274c-06e9-42a9-b555-d16696c058f0`.

Automatic approval review also rejected staging `timpactwa/Daily_Commit` as the Railway source, because persistent private-repository access and automatic deploys need explicit user approval. The service source is still null. Do not bypass this rejection. After approval and PR merges, connect `main`, use the root Dockerfile/railway.toml settings, and confirm deployment before committing the staged changes. The settings-update tool returned `Service instance not found` for the staged-only service; the checked-in config already specifies the health check and restart policy and can be applied once the service exists.

## Running locally

See [README.md](README.md) for npm, mock, real API, phone, deployment and tunnel commands. In this environment npm and Python were supplied from the bundled runtime, with test dependencies in the worktree's ignored `.venv`.

The real-API integration check resets only the demo user. Always point it at an isolated server/database. Keep the database outside Playwright's `test-results` directory because the runner clears that directory.
