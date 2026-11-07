# Daily Commit: Build Plan

Deadline: **12:00 PM, Sun 11/8/2026**. Feature freeze: **10:00 AM**. Demo: ~3 min, live on a phone.

Team: Tim (Claude Code, human lead), Liam (Codex), Rushi (Antigravity/Codex), Jordan (Codex).

---

## 1. Architecture summary

```
                 content/system-design/*.json  (Jordan, hand written, ~50)
                 content/debugging/questions.json  (Rushi, generated)
                 content/demo/demo-user.json  (Jordan, seeded demo account)
                               |
                               |  validated JSON files (contracts/validate.py)
                               v
 +-----------------+  JSON  +------------------------------+        +-------------------+
 |  /app  React    | <----> |  /api  (FastAPI)             | -----> |  SQLite (Railway  |
 |  PWA on phone   |  api.md|    reloads content + demo    |        |  volume)          |
 |  screens (Liam) |        |    user on every boot        |        |  users, ratings,  |
 |  src/api (Tim)  |        |  /engine: elo, placement,    |        |  questions(live   |
 +-----------------+        |    selection, streak (pure)  |        |  difficulty),     |
                            +------------------------------+        |  attempts,lessons |
                                                                    +-------------------+

 /pipeline (offline, Rushi):  corpus fn + (args, expected) tables --> AST mutation (one line changed)
                              --> table runner in subprocess (3 s timeout) --> keep only if a case FAILS
                              --> leak check --> emit question JSON with provenance
```

**Modules**

| Module | What it is | Runtime |
|---|---|---|
| `/app` | Mobile-first React PWA: placement, lesson player (mcq, tap_line, reorder, tap_node), feedback sheet, streak, progress. `app/src/api/` is the only code that talks HTTP | Browser on phone |
| `/api` | FastAPI routes, SQLite repo layer, content loader (runs every boot), demo endpoints | Server |
| `/engine` | Pure Python, no I/O: `elo.py`, `scoring.py`, `placement.py`, `selection.py`, `streak.py`, `readiness.py`. Unit tested against `contracts/rating.md` vectors | Imported by `/api` |
| `/pipeline` | Offline generator. 10 corpus functions with table tests, AST mutation operators, sandboxed table runner, leak check, emitter, live demo CLI | Laptop / CI |
| `/content` | JSON question banks + demo user seed | Files |

**Data flow: answer to rating to next lesson**

1. App calls `api.submitAnswer()` which sends `POST /v1/answers {lesson_id, question_id, response}`.
2. API loads the full question (with answer) from SQLite, grades it with `engine.scoring.score(format, response, answer)` giving `S` in [0,1].
3. `engine.elo.update(R_topic, Q, S, context, answers_in_topic, attempts)` returns `R'`, `Q'` (formula in `contracts/rating.md`). During placement, `engine.placement` also spills 30% of the change onto the other topics in the same track.
4. API writes in one transaction: new `user_topic_rating`, new `question.live_rating`, an `attempt` row (user, question, lesson, S, correct, time_ms, ratings before/after).
5. Response gives the app the delta, correct answer, explanation (and provenance for debugging questions, used by the terminal showcase and available for later UI).
6. `GET /v1/lessons/today` (new date) runs `engine.selection.build_lesson(...)`: weakness `W = R - 100 * misses_in_latest_lesson` picks focus topics; each slot picks the question closest to `R - 150` (~70% expected success), never repeating a debugging source function within a lesson or 3 days. `GET /v1/lessons/next/preview` runs the same thing for tomorrow without storing, which is the demo's "lesson shifted" beat. Misses count even before the lesson is finished.

**Why this protects the judged parts:** the engine is pure functions with test vectors (provably correct, easy to explain on a slide). The pipeline only keeps bugs that break a test, changes exactly one line, writes its own failure text, and rejects any question that leaks its answer, so "guaranteed correct" is demonstrable live.

---

## 2. Module ownership map

| Person | Branch | Owns (exact paths) | Never touches |
|---|---|---|---|
| **Liam** (Codex) | `app` | `app/**` except `app/src/api/**`; `.github/workflows/**`; `Dockerfile`, `railway.toml`, `scripts/tunnel.*` | `app/src/api/`, `api/`, `engine/`, `pipeline/`, `content/` |
| **Tim** (Claude Code) | `engine` | `api/**`, `engine/**`, `app/src/api/**`, `README.md` | rest of `app/`, `pipeline/`, `content/` |
| **Rushi** (Antigravity/Codex) | `pipeline` | `pipeline/**`, `content/debugging/**` | `app/`, `api/`, `engine/` |
| **Jordan** (Codex) | `content` | `content/system-design/**`, `content/demo/**`, `docs/**` (not `docs/PLAN.md`) | `app/`, `api/`, `engine/`, `pipeline/` |
| Shared | n/a | `contracts/**`, `AGENTS.md`, `CLAUDE.md`, `docs/PLAN.md`, `.github/CODEOWNERS`: change only with team agreement, Tim merges | |

Decisions behind the split:
- **Tim keeps `/engine`** so the API and engine never drift. Load relief comes from moving CI and deploy to Liam.
- **Tim owns `app/src/api/`** (typed client, mock mode, demo calls). The API's author writes its client, which removes contract drift at the source. Liam's screens import `api.*` functions and never call `fetch`.
- **Liam owns CI and deploy.** Deploy is mostly building and serving `app/dist`, which Liam knows best.
- **`content/demo/demo-user.json`** belongs to Jordan (demo story decisions stay with the demo owner); Tim's loader reads it.
- **Pipeline showcase is a terminal CLI** (`python -m pipeline demo <fn>`) owned by Rushi. No in-app provenance view and no predict-output in the app (cut to keep Liam's load bounded).
- **Task board = GitHub Issues** on `timpactwa/Daily_Commit` (one issue per task, label = milestone, assignee = owner, PR body says `Closes #N`).

---

## 3. Shared contracts

All in `/contracts`, written and validated:

| File | Contents |
|---|---|
| `question.schema.json` | JSON Schema 2020-12. Formats: `mcq`, `tap_line`, `reorder`, `tap_node`, `predict_output`. Per-format required fields and answer types. `provenance` for debugging with operators `off_by_one`, `flip_comparison`, `wrong_base_case`, `wrong_operator`, `wrong_return`, `swap_and_or`. |
| `topics.json` | 10 topics. System design: `caching`, `scaling`, `databases`, `async-messaging`, `reliability`. Debugging: `arrays-strings`, `binary-search`, `recursion`, `sorting`, `hash-maps`. |
| `api.md` | Endpoints with request/response examples, error codes, headers (`X-User-Id`, `X-Client-Date`), demo endpoints (`reset`, `advance-day`, `switch`), boot-time reload rule. |
| `rating.md` | Elo formula, K schedule, per-format scoring, 5 test vectors, placement spillover and difficulty mix, levels, readiness, lesson selection with miss pressure and repeat limits. |
| `examples/questions.json` | One valid question per main format. Mocks and engine fixtures use these. |
| `validate.py` | Schema + semantic checks: topic/track match, answer points at a real option/line/node, unique ids, `test_output` must not contain any code line, `provenance.mutated_line` must equal the answer line. Runs in CI. |

Key decisions:
- **Answers never reach the client before grading.** Server-side grading makes "guaranteed correct" real and stops answer peeking.
- **Seed vs live difficulty.** Content holds the seed `difficulty_rating`; the DB holds the live one. The boot-time reload upserts questions without resetting learned ratings.
- **Rating rule:** `E = 1/(1+10^((Q-R)/400))`, `R' = R + K_s(S-E)`, `Q' = Q - K_q(S-E)`; `K_s` = 240 placement / 48 first 10 / 24 after; `K_q = max(8, 32/(1+attempts/20))`; clamp 600..2200.
- **Placement:** 10 questions, one per topic, difficulty mix 2 easy / 4 medium / 4 hard. Each answer also moves the other 4 topics in its track by 30% of the change, so starting levels spread realistically (~1000 to 1450) even from the 4-question demo version.
- **Miss pressure:** `W = R - 100 * misses_in_latest_lesson` (current or most recent lesson, finished or not) guarantees one deliberate miss visibly shifts the preview.
- **No repeated code:** at most one question per debugging source function per lesson, none within 3 days.
- **Debugging seed difficulty:** `base[operator] + 10 * (function_lines - 8)`, base `flip_comparison 1100, wrong_operator 1150, wrong_base_case 1150, wrong_return 1150, swap_and_or 1200, off_by_one 1250`.

---

## 4. Repo structure

```
/app                          Liam (except src/api)
  src/api/client.ts           Tim: typed client for contracts/api.md
  src/api/mock.ts             Tim: fixtures from contracts/examples (VITE_MOCK=1)
  src/screens/                Onboarding, Placement, PlacementResult, Home, Lesson, LessonDone, Progress
  src/questions/              Mcq, TapLine, Reorder, TapNode, FeedbackSheet
/api                          Tim
  main.py  routes/  db.py  content_loader.py  seed_demo.py  requirements.txt  tests/
  data/                       app.db (gitignored; Railway volume in prod)
/engine                       Tim (pure python, no I/O)
  elo.py  scoring.py  placement.py  selection.py  streak.py  readiness.py  tests/
/pipeline                     Rushi
  corpus/<fn>.py              10 functions, 2 per debugging topic
  corpus/<fn>_cases.py        CASES = [((args...), expected), ...]
  mutators.py  runner.py  emitter.py  cli.py  __main__.py  tests/
/content
  system-design/<topic>.json  Jordan (10 per topic, 50 total)
  debugging/questions.json    Rushi (generated, committed snapshot)
  demo/demo-user.json         Jordan
/contracts                    shared
/docs                         Jordan: demo-script.md, pitch.md, slides; PLAN.md shared
/.github/workflows/ci.yml     Liam
/.github/CODEOWNERS           shared
Dockerfile  railway.toml  scripts/tunnel.*   Liam
AGENTS.md  CLAUDE.md  README.md
```

---

## 5. Task board

**P** = parallel, starts when its milestone opens. **B** = blocked until the listed dependency merges. Every task ends with a PR merged to main.

### M0 Setup (target: 3:30 PM Sat)

| ID | Title | Owner | Depends on | Est | P/B | Acceptance |
|---|---|---|---|---|---|---|
| S1 | Contracts, AGENTS.md, CLAUDE.md, CODEOWNERS, validator | Tim | none | done | P | `python contracts/validate.py` passes; files on main |
| S2 | Team contract review (15 min, all four); add collaborators; branch protection; real usernames in CODEOWNERS | Tim | S1 | 20m | B | Each owner signs off on the contract they consume; all four can push branches; main accepts PRs only |
| S3 | CI workflow | Liam | S2 | 30m | B | Runs validate, `pytest api engine pipeline`, `npm run build` on every PR; required check on main |
| S4 | App shell | Liam | S2 | 45m | B | Vite+React+TS+Tailwind; routing for all screens; opens on a phone via LAN URL; `npm run build` green |
| S5 | Pipeline skeleton + first 2 corpus functions with case tables | Rushi | S2 | 45m | B | `binary_search`, `factorial` pass their tables; `python -m pipeline --help` runs |
| S6 | First 5 SD questions (1/topic) + demo script outline | Jordan | S2 | 45m | B | Validates; `docs/demo-script.md` has the beats with seconds per beat |
| S7 | API client + mock mode | Tim | S2 | 60m | B | `app/src/api/` exports one typed function per endpoint in `api.md`; `VITE_MOCK=1` serves `contracts/examples`; user id + `X-Client-Date` handled inside |
| S8 | API skeleton | Tim | S2 | 30m | B | `GET /health` 200; `.gitignore` covers db, node_modules |

### M1 Thin slice (target: 6:30 PM Sat)

| ID | Title | Owner | Depends on | Est | P/B | Acceptance |
|---|---|---|---|---|---|---|
| T1 | Engine `elo.py` + `scoring.py` | Tim | S8 | 45m | P | All 5 vectors in `rating.md` pass; reorder pair-agreement scoring tested |
| T2 | Content loader (every boot, keeps live ratings) + `lessons/today` (naive) + `answers` with real Elo + users | Tim | T1 | 90m | B | curl flow: create user, get lesson, answer, rating change persisted; restart keeps live ratings |
| T3 | Lesson player: mcq + tap_line + feedback sheet | Liam | S4, S7 | 90m | B | Works in mock mode, then against local API; tapped line highlights; feedback shows delta |
| T4 | Table runner + first real mutant | Rushi | S5 | 90m | P | Runner imports a mutated fn in a subprocess, 3 s timeout, writes `fn(args): expected X, got Y`; `flip_comparison` on `binary_search` yields a question that passes validate.py |
| T5 | SD questions to 15 (3/topic, incl. 2 reorder, 2 tap_node) | Jordan | S6 | 60m | P | Validates; answers double-checked by Rushi |
| T6 | **Thin slice checkpoint** on a real phone | Tim | T2, T3, T4 | 30m | B | One SD + one generated debugging question answered on phone, rating change visible |

### M2 Core (target: midnight Sat)

| ID | Title | Owner | Depends on | Est | P/B | Acceptance |
|---|---|---|---|---|---|---|
| C1 | Placement endpoints with spillover + difficulty mix | Tim | T2 | 60m | P | `GET/POST /v1/placement` per api.md; 2 easy / 4 medium / 4 hard; spillover vector passes; `?limit=4` in demo mode |
| C2 | Lesson selection + preview | Tim | T2 | 90m | P | Tests: weakest topic gets 2 slots; one miss mid-lesson moves that topic into the preview; both tracks present; no source function repeated in a lesson or within 3 days; stable for same (user, date) |
| C3 | Placement flow + result screen | Liam | T3 | 90m | P | 10-question flow with progress bar; result shows level per topic grouped by track |
| C4 | Reorder format (tap-to-order chips) | Liam | T3 | 60m | P | Works one-handed on phone; sends id array |
| C5 | Mutation operators via `ast` | Rushi | T4 | 90m | P | off_by_one, flip_comparison, wrong_base_case, wrong_operator, wrong_return, swap_and_or; each changes exactly one existing line, same line count; unit tested |
| C6 | Filter + dedupe + leak check | Rushi | T4 | 45m | P | Keep only mutants where a case fails; drop timeouts; drop mutants with identical failure text; drop any question whose `test_output` contains a code line |
| C7 | Corpus to 10 functions (2 per debugging topic) | Rushi | S5 | 75m | P | Every original passes its table; >= 4 cases each incl. an edge case |
| C8 | Emitter + `pipeline build` + seed difficulty | Rushi | C5, C6 | 60m | B | `content/debugging/questions.json` has >= 30 valid questions across all 5 topics, provenance filled, >= 3 tagged `placement` per topic at mixed difficulty |
| C9 | SD questions to 50 (10/topic, >= 6 reorder, >= 6 tap_node, 3 placement per topic: easy/medium/hard) | Jordan | T5 | 2 x 90m | P | Validates; peer checked by Rushi; difficulty spread 900 to 1500 |
| C10 | TapNode diagram format | Liam | T3 | 75m | P | Renders flow diagram from nodes/edges; falls back to mcq list if layout fails |

### M3 Polish (target: 7:30 AM Sun)

| ID | Title | Owner | Depends on | Est | P/B | Acceptance |
|---|---|---|---|---|---|---|
| P1 | Streak + lesson complete + `me` | Tim | C2 | 45m | P | Unit tests for D-1 / same day / gap rules |
| P2 | Progress endpoint + readiness + history | Tim | C2 | 45m | P | Matches api.md shape |
| P3 | Demo mode: boot-time demo reset, `reset`, `advance-day`, `switch` + client functions | Tim | P1, P6 | 60m | B | Restart or `POST /v1/demo/reset` returns demo user to a 6-day streak in < 1 s; `api.demoSwitch()` in the client |
| P4 | Deploy on Railway with volume + tunnel script | Liam | C1, C2, C3 | 60m | B | Public HTTPS URL works on a phone over cellular; `scripts/tunnel` brings up plan B in one command |
| P5 | Home (streak flame), Lesson done, Progress screens | Liam | C3 | 90m | P | Readiness bars + sparkline; 6 to 7 streak animation on completion |
| P6 | Demo user seed `content/demo/demo-user.json` | Jordan | C9 | 45m | P | 6-day streak, placed, history that makes `recursion` the obvious next miss target |
| P7 | Mobile polish: loading, errors, retry, haptics, safe areas, PWA install, hidden switch-user (long-press logo 1 s) | Liam | P5, P3 | 90m | B | Airplane mode shows retry; Add to Home Screen opens full screen; long-press switches to demo user |
| P8 | `python -m pipeline demo <fn>` live CLI | Rushi | C8 | 60m | P | Prints original fn, cases pass, injected diff, cases fail, emitted question; under 20 s |
| P10 *(stretch)* | predict_output generator (pipeline only, not shown in app) | Rushi | C8 | 75m | P | Runs fn on a case, options = real output + outputs of 3 mutants; validates |
| P11 *(stretch)* | Spaced review slot | Tim | C2 | 45m | P | A missed question reappears the next day |
| P12 *(spare time)* | More corpus functions (light version of 20-function corpus) | Rushi | C8 | 60m | P | +4 functions, all topics still covered |

### M4 Demo (10:00 AM to 12:00 PM Sun)

| ID | Title | Owner | Depends on | Est | P/B | Acceptance |
|---|---|---|---|---|---|---|
| D1 | Demo script + pitch slides final | Jordan | S6 | 60m | P (draft early) | 3:00 timed; problem, solution, engine, pipeline, impact |
| D2 | Feature freeze, tag `demo-v1`, redeploy | Tim + Liam | M3 | 15m | B | 10:00 AM; only bug fixes after, Tim approves each |
| D3 | Backup screen recording of full flow on phone | Jordan | D2 | 30m | B | Video on two laptops + phone, plays offline |
| D4 | Rehearsal x2 (presenter Jordan, phone Liam, pipeline terminal Rushi) | All | D2 | 45m | B | Two clean runs under 3:00 with demo reset between |

**Critical path:** S2 -> S8 -> T1 -> T2 -> C2 -> P1 -> P3 -> D2. Tim's lane gates it; Liam's lane is the second longest (~11 h).

**Load estimate (agent-assisted):** Tim ~10.5 h, Liam ~11 h, Rushi ~9 h (+ stretch/spare), Jordan ~7 h.

---

## 6. Integration plan

**Checkpoints** (5-minute sync each, Tim runs it):

| Time | Checkpoint | Must be true |
|---|---|---|
| 3:30 PM Sat | M0 | Contracts signed off; collaborators added; branch protection on; CI green; 4 worktrees visible in `git worktree list` |
| 6:30 PM | M1 thin slice | T6 passes on a real phone |
| 9:00 PM | M2 midpoint | Placement works end to end; pipeline producing questions for 3+ topics |
| 12:00 AM | M2 | Full loop: placement, real selection, 50 SD + 30 debugging questions loaded |
| 7:30 AM Sun | M3 | Railway URL works; demo user resets; switch-user works; progress and streak screens |
| 10:00 AM | Freeze | `demo-v1` tagged; rehearsals start |

**Sleep shifts:** Liam and Jordan 1 to 5 AM. Tim and Rushi 3 to 7 AM. One person always overlaps to unblock. Before sleeping, leave a handoff note in your open PR. Agents left running overnight only get tasks with a clear pass/fail check (Jordan's content against validate.py, Rushi's corpus against case tables), never integration work.

**Merge rules** (branch protection on `main`):
1. PR from your module branch, one task per PR, title starts with task ID, body includes `Closes #N`.
2. Merge latest `main` into your branch and run your tests or the app first.
3. **CI green is the gate** for every PR: `python contracts/validate.py`, `pytest api engine pipeline`, `cd app && npm run build`.
4. **Human approval only where CODEOWNERS requires it:**

| Path | Approver |
|---|---|
| `/contracts/**` | Whole team agrees in chat; Tim merges |
| `/engine/**` | Rushi, checking against `rating.md` vectors |
| everything else | none; merges on green CI |

5. Squash merge. No direct pushes or force pushes to main (Tim, as admin, can bypass in an emergency only).

---

## 7. Risk list

| # | Risk | Early signal | Fallback |
|---|---|---|---|
| 1 | **Contract drift** between app and API. | T6 fails or app shows blank fields | Tim owns both the API and `app/src/api/`, so one person keeps them aligned. Mocks come from `contracts/examples`. Contracts frozen after S2; changes need a contracts PR the team approves. |
| 2 | **Pipeline yields too few or bad mutants** (equivalent mutants, infinite loops, leaks). | C8 produces < 20 questions or a topic is empty | Timeout, must-fail filter, one-line rule and leak check are in acceptance. If thin at 9 PM: P12 adds corpus functions, and a hand-reviewed `questions.json` snapshot is committed so the demo never depends on a live build. The live CLI runs on known-good `binary_search`. |
| 3 | **Tim's and Liam's lanes are both ~11 h** and the critical path runs through Tim. | M1 slips past 7 PM, or C3 not merged by midnight | App builds against mocks; pipeline and content only need validate.py. If behind at midnight: cut P11 and P10, simplify selection to "weakest topic first, closest rating" without mix slots, and Liam ships tap_node as its mcq fallback. Live demo failure is covered by D3 recording, demo reset, and the tunnel plan B. |

Also watched: venue Wi-Fi (Railway URL works over cellular; hotspot backup) and Railway problems (tunnel from a laptop).

---

## Demo flow mapping (3:00)

| Beat | Time | Screen | Backed by |
|---|---|---|---|
| Problem | 0:00-0:25 | Slide | D1 |
| Placement as a fresh user (`?limit=4`, 2 per track) | 0:25-0:55 | Placement -> result levels spread by spillover | C1, C3 |
| Long-press logo: "here's Tim on day 7" | 0:55-1:00 | Home, 6-day streak | P3, P7 |
| SD tradeoff, then tap the buggy line | 1:00-1:30 | Lesson | C2, T3 |
| Miss on purpose, open "Tomorrow" preview: topic moved up | 1:30-1:50 | Preview | C2 miss pressure |
| Finish lesson (demo user gets 3-item lessons in demo mode): streak 6 to 7 | 1:50-2:05 | Lesson done | P1, P5 |
| Pipeline live: fn, injected bug, failing case, question | 2:05-2:40 | Laptop terminal | P8 |
| Impact + close | 2:40-3:00 | Slide | D1 |
