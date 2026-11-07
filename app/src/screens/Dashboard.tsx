import { Link, Navigate, useLocation } from "react-router-dom";
import {
  api,
  getUserId,
  type CompleteResult,
  type TopicProgress,
  type User,
} from "../api";
import { Resource, topicName, useResource } from "../ui";
import { Flame } from "../Flame";
export function Home() {
  const resource = useResource(api.getMe);
  if (!getUserId()) return <Navigate to="/onboarding" replace />;
  return (
    <Resource resource={resource}>
      {(user) =>
        user.placed ? (
          <Today user={user} />
        ) : (
          <Navigate to="/placement" replace />
        )
      }
    </Resource>
  );
}
function Today({ user }: { user: User }) {
  const lesson = useResource(api.getLessonToday);
  const today = new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(new Date());
  return (
    <>
      <div className="split">
        <p className="eyebrow">{today.toUpperCase()}</p>
        <span className="tag">YOUR DAILY CHECK-IN</span>
      </div>
      <h1>
        Keep showing up,
        <br />
        {user.display_name}
        <span className="green">.</span>
      </h1>
      <p className="intro">
        Big breakthroughs start with small, daily commits.
      </p>
      <div className="dashboard-grid">
        <div>
          <div className="card lesson-card">
            <div className="split">
              <span className="eyebrow">TODAY’S COMMIT</span>
              <span className="pill">~5 MIN</span>
            </div>
            <h2>
              A little practice.
              <br />A sharper instinct.
            </h2>
            <Resource resource={lesson}>
              {(data) => (
                <>
                  <p>
                    Today, we’re focusing on{" "}
                    {data.focus_topics.map(topicName).join(" and ")}.
                  </p>
                  <div className="lesson-tags">
                    <span className="tag">◇ SYSTEM DESIGN</span>
                    <span className="tag">⌘ DEBUGGING</span>
                  </div>
                  <div className="split lesson-status">
                    <span>
                      {data.items.filter((i) => i.answered).length} /{" "}
                      {data.items.length} questions
                    </span>
                    <span>
                      {data.status === "completed"
                        ? "✓ Done for today"
                        : "Picked for your level"}
                    </span>
                  </div>
                  <Link
                    className="primary full"
                    to={data.status === "completed" ? "/progress" : "/lesson"}
                  >
                    {data.status === "completed"
                      ? "See your progress ↗"
                      : data.items.some((i) => i.answered)
                        ? "Continue practice →"
                        : "Make today’s commit →"}
                  </Link>
                </>
              )}
            </Resource>
          </div>
          <Link to="/tomorrow" className="preview-link">
            <span>
              <strong>Tomorrow is taking shape.</strong>
              <small>Your next lesson adapts to every answer.</small>
            </span>
            <span>↗</span>
          </Link>
        </div>
        <aside>
          <div className="card streak-card">
            <div className="flame" aria-hidden="true">
              <Flame size={64} animated />
            </div>
            <strong className="streak-number">
              {user.streak?.current ?? 0}
              <span> day streak</span>
            </strong>
            <p>
              {user.streak?.today_done
                ? "Today’s commit is in. See you tomorrow."
                : "A few minutes today. Momentum for tomorrow."}
            </p>
            <div
              className="streak-dots"
              aria-label={`${user.streak?.current ?? 0} day streak`}
            >
              {Array.from({ length: 7 }, (_, i) => (
                <span
                  key={i}
                  className={
                    i < Math.min(user.streak?.current ?? 0, 7) ? "filled" : ""
                  }
                >
                  {i < Math.min(user.streak?.current ?? 0, 7) ? "✓" : "·"}
                </span>
              ))}
            </div>
          </div>
          <div className="quiet-note">
            <p className="eyebrow">CONSISTENCY &gt; INTENSITY</p>
            <p>
              You don’t need to know everything.
              <br />
              Just a little more than yesterday.
            </p>
          </div>
        </aside>
      </div>
      <div className="footer-note">
        <span className="green">●</span> Built around your weak spots. Growing
        at your pace.
      </div>
    </>
  );
}
function Sparkline({ history }: { history: number[] }) {
  if (history.length < 2)
    return <span className="small">Your trend starts with practice.</span>;
  const low = Math.min(...history) - 10;
  const high = Math.max(...history) + 10;
  const points = history
    .map(
      (v, i) =>
        `${(i / (history.length - 1)) * 100},${34 - ((v - low) / (high - low)) * 28}`,
    )
    .join(" ");
  return (
    <svg
      className="sparkline"
      viewBox="0 0 100 40"
      role="img"
      aria-label={`Rating trend: ${history.map(Math.round).join(", ")}`}
    >
      <polyline fill="none" stroke="#81a547" strokeWidth="2" points={points} />
    </svg>
  );
}
/** Where a topic's rating came from: nothing yet, placement only, or real answers. */
function ratingState(topic: TopicProgress): "unrated" | "placement" | "rated" {
  if (topic.answered > 0) return "rated";
  return Math.round(topic.rating) === 1200 && topic.history.length === 0 ? "unrated" : "placement";
}
function TopicCard({ topic }: { topic: TopicProgress }) {
  const state = ratingState(topic);
  return (
    <article className={`topic-progress ${state}`}>
      <div className="split">
        <strong>{topicName(topic.topic)}</strong>
        {state === "unrated" ? (
          <span className="level new">New</span>
        ) : (
          <span className={`level ${topic.level}`}>{topic.level}</span>
        )}
      </div>
      <div className="split">
        {state === "unrated" ? (
          <p className="unrated-note">Not rated yet</p>
        ) : (
          <p>
            <b>{topic.readiness}%</b> readiness
          </p>
        )}
        {state === "rated" && <Sparkline history={topic.history} />}
      </div>
      <progress
        max={100}
        value={state === "unrated" ? 0 : topic.readiness}
        aria-label={`${topicName(topic.topic)} readiness`}
      />
      <div className="rating-row">
        {state === "unrated" && (
          <span className="rating-hint">Answer a question in this topic to get your first rating.</span>
        )}
        {state === "placement" && (
          <>
            <span className="rating-chip">
              <b>{Math.round(topic.rating)}</b> rating
            </span>
            <span className="rating-hint">Estimate from your placement test</span>
          </>
        )}
        {state === "rated" && (
          <>
            <span className="rating-chip">
              <b>{Math.round(topic.rating)}</b> rating
            </span>
            <span className="rating-hint">
              {topic.answered} {topic.answered === 1 ? "answer" : "answers"} · {Math.round(topic.accuracy * 100)}% correct
            </span>
          </>
        )}
      </div>
    </article>
  );
}
export function Progress() {
  const resource = useResource(api.getProgress);
  if (!getUserId()) return <Navigate to="/onboarding" replace />;
  return (
    <Resource resource={resource}>
      {(data) => (
        <>
          <p className="eyebrow">THE BIGGER PICTURE</p>
          <h1>
            Progress, one
            <br />
            commit at a time.
          </h1>
          <div className="readiness-banner card">
            <div>
              <p className="eyebrow">OVERALL READINESS</p>
              <strong>
                {data.overall_readiness}
                <span>%</span>
              </strong>
            </div>
            <div>
              <p>
                {data.streak.current} day streak · Best: {data.streak.best} days
              </p>
              <p className="small">
                Your starting point is a chapter, not the whole story.
              </p>
            </div>
          </div>
          {(["system-design", "debugging"] as const).map((track) => (
            <section className="track-section" key={track}>
              <h2>
                {track === "system-design" ? "◇ System design" : "⌘ Debugging"}
              </h2>
              <div className="topic-grid">
                {data.topics
                  .filter((t) => t.track === track)
                  .map((t) => (
                    <TopicCard topic={t} key={t.topic} />
                  ))}
              </div>
            </section>
          ))}
        </>
      )}
    </Resource>
  );
}
export function LessonDone() {
  const { state } = useLocation();
  const result = state as CompleteResult | null;
  if (!result?.streak || !result.summary) return <Navigate to="/" replace />;
  return (
    <section className="done">
      <p className="eyebrow">TODAY’S COMMIT: COMPLETE</p>
      <div
        className={`flame celebration ${result.streak.extended ? "extended" : ""}`}
        aria-hidden="true"
      >
        <Flame size={88} animated />
      </div>
      <h1>
        You showed up.
        <br />
        That’s what counts.
      </h1>
      <div
        className="streak-total"
        aria-label={`${result.streak.current} day streak`}
      >
        {result.streak.extended && result.streak.current > 1 && (
          <span className="streak-before">{result.streak.current - 1} → </span>
        )}
        <strong>{result.streak.current}</strong>
        <span> day streak</span>
      </div>
      <p>
        {result.summary.correct} of {result.summary.total} answers correct. A
        little stronger than yesterday.
      </p>
      <div className="card changes">
        {result.rating_changes.map((change) => (
          <div className="topic-row" key={change.topic}>
            <strong>{topicName(change.topic)}</strong>
            <span>
              {Math.round(change.before)} → <b>{Math.round(change.after)}</b>
            </span>
          </div>
        ))}
      </div>
      <Link className="primary full" to="/tomorrow">
        See what’s next →
      </Link>
      <Link className="text-link" to="/progress">
        View my progress
      </Link>
    </section>
  );
}
export function Tomorrow() {
  const resource = useResource(api.getNextPreview);
  return (
    <section className="practice">
      <Link to="/" className="back">
        ← Today
      </Link>
      <p className="eyebrow">ALWAYS ADAPTING</p>
      <h1>
        Tomorrow starts
        <br />
        with today.
      </h1>
      <p>
        Every answer helps shape your next lesson. Here’s where we’ll focus
        next.
      </p>
      <Resource resource={resource}>
        {(data) => (
          <>
            <div className="card">
              <p className="eyebrow">NEXT UP · {data.date}</p>
              {data.focus_topics.map((focus) => (
                <div className="focus-item" key={focus.topic}>
                  <span className="focus-dot">↗</span>
                  <div>
                    <h2>{topicName(focus.topic)}</h2>
                    <p>
                      {focus.reason === "missed_last_lesson"
                        ? "A little extra practice after a recent miss."
                        : "A chance to strengthen your foundation."}
                    </p>
                  </div>
                  <span className="pill">{Math.round(focus.rating)} Elo</span>
                </div>
              ))}
            </div>
            <p className="small">
              {data.items.length} questions · A mix of system design and
              debugging · Shaped around you
            </p>
          </>
        )}
      </Resource>
      <Link className="text-link" to="/lesson">
        Back to today’s practice →
      </Link>
    </section>
  );
}
