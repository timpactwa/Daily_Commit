# Daily Commit: Jordan's spoken script

Use [the runbook](demo-script.md) for actions. Pause while Liam answers. Windows include speech and interaction; the 3:00 timing remains a target until two human rehearsals pass.

## 0:00–0:25 · Problem and solution · Slides 1–2

“Interview prep is easy to postpone. A long problem set feels like tomorrow's job, and debugging deserves practice too. We built Daily Commit: five minutes of daily interview practice, across system design and debugging, with questions selected for your level.”

## 0:25–0:55 · Placement · Phone

“A short placement gives us a starting map. Each answer updates its topic and related topics in the same track. Watch the levels spread out.”

Pause for four answers and results. If placement overruns, use the returning-user recovery cue.

## 0:55–1:00 · Returning user · Phone

“Here is Tim a week in, with a six-day streak.”

## 1:00–1:30 · Both tracks and the engine · Phone

“System design asks about tradeoffs. Debugging asks you to find the faulty line. Every answer updates your topic rating and the question's difficulty, using Elo. Our debugging pipeline starts with passing code and keeps an injected bug only when a test fails.”

Describe the track actually visible. Q1 and Q2 can appear in either order. Leave time for both feedback sheets.

## 1:30–1:50 · Deliberate miss and preview · Phone

“I'll miss this one deliberately. Now look at tomorrow: that topic gets extra practice immediately, even before I finish today's lesson.”

Name Q3's displayed topic. Show its recent-miss reason and return to practice.

## 1:50–2:05 · Completion · Phone

“Finish the lesson, and six days becomes seven. The habit is the same. The next lesson adapts.”

## 2:05–2:40 · Verified pipeline · Terminal

“Here is the generator live. The original function passes its tests. We change one existing line. The same tests now fail, and the changed line becomes the question's answer. Candidates that still pass or time out get discarded. The failure text comes from our runner, so the learner sees the failing case without a traceback revealing the code.”

Leave time for output. Introduce fallback text as “a saved run”.

## 2:40–2:53 · Evidence · Slide 5

“In a simulation of 300 students over fourteen days, question difficulty error falls from 119 to 52 Elo points. That tests calibration. Real student outcomes are our next test.”

## 2:53–3:00 · Close · Slide 6

“Next, we expand the corpus and test with students. Five minutes a day, matched to you. Daily Commit.”

## Judge questions

| Question | Answer |
|---|---|
| What does verification guarantee? | The original passes the supplied cases, a mutation changes one existing line, and the retained mutant fails a case. The answer is that changed line. This does not prove exhaustive correctness or pedagogical quality. |
| Why Elo? | One update estimates student topic skill and question difficulty. Content seeds difficulty; live question ratings learn from answers. |
| Why 150 points below the student? | Elo predicts about 70% at that gap. This is the selection target. The finite synthetic bank realizes about 60% in our simulation. |
| Does simulation show students learning? | No. True skill stays fixed. It measures estimation and calibration under simulated responses, not retention or interview performance. |
| What changes after a miss? | Selection subtracts 100 points per recent miss when ranking topic weakness. The preview uses it before lesson completion. |
| How do you avoid repeated code? | At most one debugging question per source function per lesson; recent functions are excluded over three days. |
| Why is the deliberate miss not always recursion? | Recursion starts weak and may already be a focus topic. Q3 comes from the mix slot, making its new miss visible in the preview. |
| How much content exists? | Currently 50 curated system-design questions and 54 generated debugging questions. Recount if the bank changes. |
| What's next? | More tested source functions and student trials. Spaced review already exists. Leaderboards and richer generation remain future ideas. |

Reproducible claims: [demo-evidence.md](demo-evidence.md). Slides: [daily-commit-pitch.pptx](daily-commit-pitch.pptx). Slides 3–4 support questions and recovery; the normal stage sequence uses the phone and terminal instead.
