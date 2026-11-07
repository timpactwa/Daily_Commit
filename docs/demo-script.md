# Demo Script (3:00)

Roles: **Jordan** presents, **Liam** drives the phone (screen mirrored), **Rushi** drives the laptop terminal.
Talk track for each beat is in [`pitch.md`](pitch.md). Times are cumulative.

## Before going on stage (T-10 min)

1. Open the deployed URL on the phone (Railway) and check `GET /health` shows `"ok": true` and a question count above 80.
2. Phone: clear site data (or use a private tab) so the app starts as a brand-new user.
3. Laptop: terminal open in the repo, font size 20+, command typed but not run: `python -m pipeline demo binary_search`.
4. Laptop: slides open on slide 1. Backup video (D3) open in a second window, paused at 0:00.
5. Rehearsed once in the last hour. Server is in `DEMO_MODE=1`.

## Beats

| Time | Beat | Who | Exact actions | What the audience must see |
|---|---|---|---|---|
| 0:00 | Problem | Jordan | Slide 1 | Prep is scattered, cram-based, and skips debugging |
| 0:25 | Placement | Liam | Open app, enter a name, take the **4-question** placement (demo mode). Answer 2 right, 2 wrong. | Result screen: levels per topic that differ from each other |
| 0:55 | Switch to day 7 | Liam | **Long-press the logo for 1 s** | Home shows "Tim", streak **6** |
| 1:00 | Lesson: tradeoff | Liam | Start lesson. Q1 (system design): answer **correctly** | Feedback sheet, rating goes **up** |
| 1:15 | Lesson: tap the bug | Liam | Q2 (tap the buggy line): tap the **correct** line | Line highlights, failing test shown, rating up |
| 1:30 | Miss on purpose | Liam | Q3: answer **wrong** on purpose | Rating goes down |
| 1:40 | Lesson shifts | Liam | Lesson done screen, open **Tomorrow** | Q3's topic now in tomorrow's focus, labeled "you missed this" |
| 1:50 | Streak | Liam | (same screen) | Streak animates **6 to 7** |
| 2:05 | Pipeline live | Rushi | Run `python -m pipeline demo binary_search` | Working function, tests pass, injected one-line bug, tests fail, emitted question |
| 2:40 | Impact + close | Jordan | Slides 5-6 | Simulation result, what's next |
| 3:00 | End | | | |

**Rule for Q3:** always miss the **third** question. It is the "mix" item, from a topic not already in focus, so the shift in tomorrow's lesson is visible.

## If something breaks

| Problem | Do this, without stopping the talk |
|---|---|
| Deployed URL down | Liam switches to the laptop tunnel URL (`scripts/tunnel`, plan B) |
| Placement or lesson screen errors | Long-press logo (switch user) and continue from the lesson beat |
| Lesson already completed (someone rehearsed today) | Long-press logo again: switch resets the demo user to a fresh day 7 |
| Pipeline command fails | Rushi shows the last saved run output (`docs/pipeline-demo-output.txt`) |
| Everything is down | Jordan: "Here's a recording from 20 minutes ago." Play the backup video |

## Reset between rehearsals

- Phone: long-press logo (resets the demo user to streak 6, nothing answered).
- For the fresh-user placement beat: clear site data or open a new private tab.
- Server restart also resets the demo user.
