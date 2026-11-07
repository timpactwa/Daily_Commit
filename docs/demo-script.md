# Daily Commit stage runbook (3:00)

Jordan presents and advances slides. Liam drives the mirrored phone. Rushi drives the terminal. The [spoken script](pitch.md), [editable deck](daily-commit-pitch.pptx), and [evidence](demo-evidence.md) cover D1 (#36).

## Preflight (T-10 minutes)

1. Confirm the deployment uses `DEMO_MODE=1` and the real API (`VITE_MOCK` off). `/health` must report `ok: true` and the expected loaded bank, currently 104 questions. Health alone does not prove demo mode works.
2. On the phone, use a fresh private session. Check placement has **4 questions**. Rehearse the answers using feedback, since IDs, formats and option order can vary.
3. Hold the logo for one second. Confirm **Tim**, streak **6**, and an unanswered **3-item** lesson. Rehearse Q1/Q2 correctly and Q3 incorrectly. Note Q3's topic and verify Tomorrow's recent-miss reason.
4. Reset with another logo hold. Use a new private session for the stage's fresh-user placement. Keep the date, deployment and phone unchanged after rehearsal.
5. Rushi: repo-root terminal, dependencies ready, font 20+ pt. Run `python -m pipeline demo binary_search` once and leave the command ready. Open [saved output](pipeline-demo-output.txt) offline as a fallback.
6. Jordan: open the deck in presentation mode. Normal display sequence: slide 1, slide 2, phone, terminal, slide 5, slide 6. Slides 3 and 4 support technical questions or a failed live display.
7. Confirm the phone backup video plays locally on both laptops and the phone. Follow [recording-checklist.md](recording-checklist.md). Do not claim the recording exists until those checks pass.

## Cumulative stopwatch cues

| Time | Seconds | Display | Action and visible proof |
|---|---:|---|---|
| 0:00–0:18 | 18 | Slide 1 | Jordan introduces the consistency problem. |
| 0:18–0:25 | 7 | Slide 2 | Introduce daily practice across both tracks. |
| 0:25–0:55 | 30 | Phone: placement | Four answers, two right and two wrong. Submit and show different topic levels. Rehearse answers for the current questions. |
| 0:55–1:00 | 5 | Phone: Home | Hold logo one second. Show Tim, streak 6. |
| 1:00–1:15 | 15 | Phone: Q1 | Tap “Make today’s commit”. Correct answer, “Check answer”, then “Continue”. Show positive rating feedback. |
| 1:15–1:30 | 15 | Phone: Q2 | Correct answer and continue. The first two items include system design and tap-the-line debugging; their order can vary. Describe the track actually visible. |
| 1:30–1:40 | 10 | Phone: Q3 | Deliberately miss the **third (mix)** item. Show negative feedback, name its topic, then continue. It need not be recursion. |
| 1:40–1:50 | 10 | Phone: Tomorrow | Before finishing, tap “See how tomorrow’s lesson is adapting”. Show Q3's topic with “A little extra practice after a recent miss.” Tap “Back to today’s practice”. |
| 1:50–2:05 | 15 | Phone: completion | Tap “Finish lesson”. Show streak **6 to 7**. The final answer alone does not finish the lesson. |
| 2:05–2:40 | 35 | Terminal | Rushi runs `python -m pipeline demo binary_search`. Original passes, one changed line, failing cases, emitted question. The terminal intentionally reveals the answer. |
| 2:40–2:53 | 13 | Slide 5 | 119 to 52 Elo difficulty error. Say **simulation**, 300 students, 14 days. Calibration evidence, not student learning gains. |
| 2:53–3:00 | 7 | Slide 6 | Close and stop at 3:00. |
| **Total** | **180** | | Two timed human rehearsals remain required. |

Always miss Q3. Do not promise system design first or a recursion miss. Show the missed topic and its reason rather than claiming every other focus topic changed.

## Recovery

| Failure | Continue with |
|---|---|
| Deployment down | Liam opens the already-rehearsed tunnel URL. On Windows: `./scripts/tunnel.ps1 -SkipBuild` after building the app and installing cloudflared. Keep that laptop running. |
| Placement errors or takes too long | Hold logo. Say “Here is a returning user”, resume at 0:55. |
| Lesson already answered | Hold logo again. Confirm streak 6 and 0/3 before resuming. Switching resets the demo account. |
| Preview differs from rehearsal | Describe the visible result. Use the backup clip if ready rather than claiming an unseen shift. |
| Pipeline fails or exceeds 20 seconds | Show `docs/pipeline-demo-output.txt`. Introduce it as **a saved run**. |
| Mirroring fails | Play the local recording and identify it as a recording. If D3 remains pending, use slides 3 and 4 to explain the mechanisms. |
| Running behind | Cut optional transitions and Q&A. Preserve miss, preview, streak and pipeline proof. |

## Reset and rehearsal record

Logo hold resets Tim to six days and an unanswered lesson. Server restart also resets him. Demo reset preserves learned question ratings, so question choices can change between rehearsals. Fresh-user placement needs a separate private session.

| Run | Build/tag | Date/device | Elapsed | Missed topic in preview | Streak 7 | Pipeline <20 s | Initials |
|---|---|---|---|---|---|---|---|
| 1 | pending | pending | pending | pending | pending | pending | pending |
| 2 | pending | pending | pending | pending | pending | pending | pending |
