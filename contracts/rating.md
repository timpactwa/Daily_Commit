# Rating Rule (contract v1)

Every rated answer updates two numbers: the student's rating for that question's topic, and the question's difficulty rating. Elo-style, same scale for both.

## Constants

| Name | Value | Meaning |
|---|---|---|
| `R0` | 1200 | Starting rating for every (user, topic) |
| `K_PLACEMENT` | 240 | Student K during the placement test |
| `K_NEW` | 48 | Student K for the first 10 rated answers in a topic after placement |
| `K_SETTLED` | 24 | Student K after that |
| `K_Q_MAX` | 32 | Question K when the question has 0 attempts |
| `K_Q_MIN` | 8 | Question K floor |
| `R_MIN`, `R_MAX` | 600, 2200 | Clamp for all ratings |
| `TARGET_GAP` | 150 | Lesson aims for questions ~150 below the student (~70% expected success) |
| `DIFFICULTY_TOLERANCE` | 150 | Max distance from target before a slot moves to another topic |
| `SPILLOVER` | 0.3 | Placement only: share of a topic's change applied to the other topics in its track |

## Formula

```
E  = 1 / (1 + 10 ** ((Q - R) / 400))        # expected score for student R on question Q
S  = score in [0, 1]                         # see "Scoring" below

K_s = K_PLACEMENT                 if context == "placement"
      K_NEW                       if answers_in_topic < 10
      K_SETTLED                   otherwise
K_q = max(K_Q_MIN, K_Q_MAX / (1 + attempts / 20))   # attempts = prior attempts on this question

R' = clamp(R + K_s * (S - E))
Q' = clamp(Q - K_q * (S - E))
```

Ratings are stored as floats and displayed rounded to an int.

## Scoring (S)

| Format | S | `correct` |
|---|---|---|
| `mcq`, `predict_output`, `tap_node` | 1 if response == answer else 0 | S == 1 |
| `tap_line` | 1 if response == answer else 0 | S == 1 |
| `reorder` | fraction of item pairs in the correct relative order (Kendall agreement), rounded to 2 dp | S == 1 |

## Test vectors (engine unit tests must pass these)

| R | Q | context | answers_in_topic | attempts | S | R' | Q' |
|---|---|---|---|---|---|---|---|
| 1200 | 1200 | placement | 0 | 0 | 1 | 1320.0 | 1184.0 |
| 1200 | 1200 | placement | 0 | 0 | 0 | 1080.0 | 1216.0 |
| 1200 | 1050 | lesson | 3 | 0 | 0 | 1166.24 | 1072.51 |
| 1400 | 1250 | lesson | 15 | 20 | 1 | 1407.12 | 1245.25 |
| 1200 | 1400 | placement | 0 | 0 | 1 | 1382.34 | 1375.69 |

(Values to 2 dp. Rows 3 and 4: E = 0.7034. Row 3: K_s = 48, K_q = 32. Row 4: K_s = 24, K_q = 16. Row 5: E = 0.2403; with spillover, each other topic in the same track that started at 1200 ends at 1254.70.)

## Levels and readiness (display only)

```
level      = "beginner" if R < 1150 else "intermediate" if R < 1300 else "advanced"
readiness  = clamp(round((R - 900) / 700 * 100), 0, 100)       # per topic, 0..100
overall    = mean(readiness over all 10 topics)
```

## Lesson selection (engine behavior, informative)

Owned by `/engine`; documented here so the app and content owners know what to expect. Lesson = 6 items.

1. **Weakness score** per topic: `W = R_topic - 100 * misses_in_latest_lesson(topic)`, where the latest lesson is the current or most recent lesson, completed or not. Lowest W = weakest. The miss pressure term makes one deliberate miss visibly shift the next lesson, even before the lesson is finished.
2. **Slots:** 2 focus items from weakest topic, 1 from second weakest, 2 mix items (guarantee both tracks appear), 1 review item (most recent missed question answered on an earlier day; if none, another focus item).
3. **Pick per slot:** target `Q* = R_topic - TARGET_GAP`. Candidates are questions in that topic not answered in the last 3 days and not already in the lesson. Debugging candidates also exclude any question whose `provenance.source_function` is already in this lesson or was shown to the user in the last 3 days (no seeing the same code twice). Rank by `|Q - Q*|`, choose randomly among the best 3 with seed `hash(user_id, date)` so a lesson is stable for the day.
   **Tolerance:** a slot first only accepts questions within `DIFFICULTY_TOLERANCE = 150` of `Q*`. If a topic has none (its near-target questions are used up), the slot moves to the next topic in line; only if no topic has one does it take the closest question anywhere. Exception: a topic missed in the latest lesson always gets one item regardless of tolerance, so a miss visibly shifts the next lesson. Simulation (`python -m engine.simulate`) shows this keeps real success near 60% and steady instead of ~49% and sliding.
4. **Order:** start with the easiest item, end with a mix item (finish on a likely win).
5. A lesson is generated once per (user, date) and stored. The preview endpoint runs the same selection against current ratings for tomorrow without storing.

## Placement

10 questions, one per topic, from questions with `placement: true`. Difficulty mix across the 10: 2 easy (~1000), 4 medium (~1200), 4 hard (~1400), shuffled; each track gets at least one of each.

Every rating starts at `R0`. Answers are applied in order with `K_PLACEMENT`:

```
delta = K_PLACEMENT * (S - E)
R[topic]       += delta
R[other topic in same track] += SPILLOVER * delta     # SPILLOVER = 0.3, for each of the other 4
```

So one answer informs related skills, and placement ends with a spread of levels (roughly 1000 to 1450) instead of two values. In the demo, `?limit=4` gives 2 per track; spillover still moves every topic.
