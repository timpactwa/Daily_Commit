# Demo evidence and limits

D1 (#36). Checked against main through `d607115` on 7 November 2026. The engine, API and content sources used below are unchanged from `1880ed6`. This file records implementation checks, not a completed human stage rehearsal.

## Content and integration

- The bank contains **50 system-design** questions (10 per topic) and **54 debugging** questions, 104 total. The content validator checks these plus four contract fixtures: **108 checked, 0 failing**.
- `python -m pytest api engine pipeline -q`: **148 passed**. This includes `api/tests/test_real_demo.py` over **30 dates**, plus the synthetic beat-by-beat demo test.
- The real-content test verifies a three-item demo lesson with both tracks, Q1/Q2 correct, deliberate Q3 mix miss, the missed topic in the preview with `missed_last_lesson`, and completed streak 7. Q1/Q2 order and the mix topic are not fixed.
- Local TypeScript, Vite and PWA production build passed. Node dependencies were installed with pnpm because this workstation has no npm command. GitHub CI runs the repository's canonical `npm ci` and full build from `app/package-lock.json`; its result is the merge gate.
- Button labels and navigation in the runbook match `app/src/screens/Lesson.tsx`, `Dashboard.tsx`, `Logo.tsx`, and `questions/FeedbackSheet.tsx`. Preview happens before “Finish lesson”, then returns to practice for streak completion.

Reproduce with Python 3.12 and `api/requirements.txt` installed:

```text
python contracts/validate.py
python -m pytest api engine pipeline -q
cd app
npm ci
npm run build
```

## Simulation

[Raw output](simulation-output.txt) comes from:

```text
PYTHONHASHSEED=0 python -m engine.simulate --students 300 --days 14 --seed 1
```

PowerShell equivalent: set `$env:PYTHONHASHSEED='0'` before the Python command. The hash seed fixes track iteration order as well as the simulation's explicit random seed.

| Measure | Result |
|---|---:|
| Synthetic students | 300 |
| Simulated days per student | 14 |
| Synthetic question bank | 120 |
| Mean absolute question difficulty error at seed | 119 Elo points |
| Mean absolute question difficulty error after answers | 52 Elo points |
| Lesson success, first three days | 61% |
| Lesson success, last three days | 59% |

These rounded values measure **rating calibration under simulated answers**. True student skills stay fixed. The run does not measure student learning, retention, interview readiness, or outcomes from real users. Its bank is synthetic and differs from the 104-question product bank. The ~70% figure is Elo's expected score at a 150-point rating gap, not observed success in this run.

## Pipeline

[Saved plain-text run](pipeline-demo-output.txt):

```text
python -m pipeline demo binary_search --no-color --save docs/pipeline-demo-output.txt
```

Measured locally at **10.58 seconds**, exit 0, with normal presentation pauses enabled. Six original cases pass. Of twelve candidate bugs, seven break a case, two still pass and three time out. The showcased comparison changes line 4 from `while lo <= hi:` to `while lo < hi:`. Three of six cases fail, including `search([4], 4): expected 0, got -1`.

Verification establishes a defect against supplied cases and identifies the one changed line. It does not prove exhaustive correctness. The live terminal deliberately reveals the answer; the learner's pre-grading question does not contain the answer field. The saved run is an offline terminal fallback and must be introduced as saved output.

## Presentation and outstanding human checks

The six-slide editable PowerPoint includes speaker notes with source links and timing cues. Its product screenshot comes from the actual local app in **mock mode**; it is an illustrative product view, not evidence of production connectivity. The chart uses the simulation values above.

D1 provides the timed script, deck, exact operator cues and fallbacks. Two live rehearsals remain D4 work. D3 (#38) remains **pending D2 (#37)** and actual phone capture plus offline playback on both laptops and the phone. Use [the recording checklist](recording-checklist.md). No recording, rehearsal result or deployed readiness is claimed here.
