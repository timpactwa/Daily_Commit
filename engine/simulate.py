"""Does the engine learn? Simulated students with hidden true skill go through placement and
daily lessons. We track how close ratings get to the truth and the real success rate.

    python -m engine.simulate                 # 200 students, 14 days
    python -m engine.simulate --students 500 --days 21 --seed 7

Model: a student's true skill per topic = track ability + topic offset (so related topics move
together, which is what placement spillover assumes). Questions have a true difficulty; their
seed rating is the truth plus author error (sd 150), as if a human guessed. P(correct) is the
Elo logistic of (true skill, true difficulty).
"""
import argparse
import random
import statistics
from dataclasses import dataclass

from engine import elo, placement
from engine.selection import Candidate, History, build_lesson

SD = ["caching", "scaling", "databases", "async-messaging", "reliability"]
DBG = ["arrays-strings", "binary-search", "recursion", "sorting", "hash-maps"]
TOPIC_TRACK = {**{t: "system-design" for t in SD}, **{t: "debugging" for t in DBG}}
QUESTIONS_PER_TOPIC = 12
SEED_ERROR = 150.0


@dataclass
class Q:
    id: str
    topic: str
    track: str
    true: float
    rating: float
    attempts: int = 0
    source_function: str | None = None


def make_questions(rng: random.Random) -> dict[str, Q]:
    qs = {}
    for t, tr in TOPIC_TRACK.items():
        for i in range(QUESTIONS_PER_TOPIC):
            true = rng.gauss(1200, 180)
            fn = f"{t}-fn{i // 3}" if tr == "debugging" else None
            qs[f"{t}-{i}"] = Q(f"{t}-{i}", t, tr, true, elo.clamp(true + rng.gauss(0, SEED_ERROR)), source_function=fn)
    return qs


def make_student(rng: random.Random) -> dict[str, float]:
    track_ability = {tr: rng.gauss(1200, 150) for tr in set(TOPIC_TRACK.values())}
    return {t: track_ability[tr] + rng.gauss(0, 80) for t, tr in TOPIC_TRACK.items()}


def pool(qs: dict[str, Q]) -> list[Candidate]:
    return [Candidate(q.id, q.topic, q.track, q.rating, q.source_function) for q in qs.values()]


def answer(rng, true_skill: float, q: Q) -> float:
    return 1.0 if rng.random() < elo.expected(true_skill, q.true) else 0.0


def mean_abs(xs) -> float:
    return statistics.fmean(abs(x) for x in xs)


def run(students: int = 200, days: int = 14, seed: int = 1) -> dict:
    rng = random.Random(seed)
    qs = make_questions(rng)
    q_err_start = mean_abs(q.rating - q.true for q in qs.values())
    errors_by_day: list[list[float]] = [[] for _ in range(days + 2)]
    success_by_day: list[list[float]] = [[] for _ in range(days + 1)]

    for s in range(students):
        truth = make_student(rng)
        ratings = {t: elo.R0 for t in TOPIC_TRACK}
        answers_in_topic = {t: 0 for t in TOPIC_TRACK}
        errors_by_day[0].append(mean_abs(ratings[t] - truth[t] for t in TOPIC_TRACK))

        for c in placement.choose(pool(qs), TOPIC_TRACK, seed=f"s{s}"):
            q = qs[c.id]
            u = elo.update(ratings[q.topic], q.rating, answer(rng, truth[q.topic], q), "placement", 0, q.attempts)
            ratings[q.topic] = u.student_after
            ratings.update(placement.spillover(ratings, q.topic, u.student_delta, TOPIC_TRACK))
            q.rating, q.attempts = u.question_after, q.attempts + 1
        errors_by_day[1].append(mean_abs(ratings[t] - truth[t] for t in TOPIC_TRACK))

        recent: list[set[str]] = []
        misses: dict[str, int] = {}
        for day in range(days):
            hist = History(misses_in_latest_lesson=misses, recently_answered=set().union(*recent[-3:]) if recent else set())
            picks = build_lesson(ratings, pool(qs), hist, seed=f"s{s}:d{day}")
            misses, today, wins = {}, set(), []
            for p in picks:
                q = qs[p.question_id]
                sc = answer(rng, truth[q.topic], q)
                u = elo.update(ratings[q.topic], q.rating, sc, "lesson", answers_in_topic[q.topic], q.attempts)
                ratings[q.topic] = u.student_after
                answers_in_topic[q.topic] += 1
                q.rating, q.attempts = u.question_after, q.attempts + 1
                if sc < 1:
                    misses[q.topic] = misses.get(q.topic, 0) + 1
                today.add(q.id)
                wins.append(sc)
            recent.append(today)
            success_by_day[day + 1].append(statistics.fmean(wins) if wins else 0)
            errors_by_day[day + 2].append(mean_abs(ratings[t] - truth[t] for t in TOPIC_TRACK))

    return {
        "student_error": [statistics.fmean(e) for e in errors_by_day],
        "success": [statistics.fmean(x) for x in success_by_day[1:]],
        "question_error_start": q_err_start,
        "question_error_end": mean_abs(q.rating - q.true for q in qs.values()),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--students", type=int, default=200)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    r = run(a.students, a.days, a.seed)
    e = r["student_error"]
    print(f"{a.students} simulated students, {a.days} days, 10 topics, {QUESTIONS_PER_TOPIC * 10} questions\n")
    print("Average error between a student's rating and their true skill (Elo points):")
    print(f"  before placement     {e[0]:6.0f}")
    print(f"  after placement      {e[1]:6.0f}   (10 questions)")
    for d in (1, 3, 7, a.days):
        if d <= a.days:
            print(f"  after day {d:<3}        {e[d + 1]:6.0f}")
    print("\nReal success rate in lessons (target ~70%):")
    print(f"  days 1-3  {statistics.fmean(r['success'][:3]):.0%}    last 3 days  {statistics.fmean(r['success'][-3:]):.0%}")
    print("\nQuestion difficulty error (author's guess vs learned):")
    print(f"  seed {r['question_error_start']:.0f}  ->  learned {r['question_error_end']:.0f} Elo points")


if __name__ == "__main__":
    main()
