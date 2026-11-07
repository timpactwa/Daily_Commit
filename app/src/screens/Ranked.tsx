import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  api,
  ApiError,
  type RankedResult,
  type RankedSession,
  type RankedTier,
  type ResponseValue,
  type TierId,
} from "../api";
import { isComplete, Question } from "../questions/Question";
import { clockText, ErrorNotice, Loading, Resource, Rich, useResource } from "../ui";

const TIERS: TierId[] = ["beginner", "intermediate", "advanced"];
const tierParam = (raw?: string): TierId => (TIERS.includes(raw as TierId) ? (raw as TierId) : "beginner");

export function RankedHome() {
  const resource = useResource(api.getRanked);
  return (
    <section className="ranked">
      <p className="eyebrow">RANKED</p>
      <h1>
        One shot. Same test for everyone<span className="green">.</span>
      </h1>
      <p className="intro">
        Ten standardized questions on a clock. Each test can be taken once, so the leaderboard stays fair.
      </p>
      <Resource resource={resource}>
        {({ has_account, tiers }) => (
          <>
            {!has_account && (
              <div className="card account-banner">
                <strong>Create an account to compete.</strong>
                <p>Ranked results are tied to your username. Your practice progress comes with you.</p>
                <Link to="/account" className="primary">
                  Create account →
                </Link>
              </div>
            )}
            <div className="tier-grid">
              {tiers.map((t) => (
                <TierCard key={t.id} tier={t} canStart={has_account} />
              ))}
            </div>
          </>
        )}
      </Resource>
    </section>
  );
}

function TierCard({ tier: t, canStart }: { tier: RankedTier; canStart: boolean }) {
  const [confirming, setConfirming] = useState(false);
  const navigate = useNavigate();
  const a = t.attempt;
  return (
    <article className={`card tier-card tier-${t.id}`}>
      <div className="split">
        <strong className="tier-title">{t.title}</strong>
        {t.suggested && !a && <span className="pill">SUGGESTED</span>}
        {a?.status === "finished" && <span className="pill learned">TAKEN</span>}
      </div>
      <p>{t.description}</p>
      <p className="small muted">
        {t.question_count} questions · {Math.round(t.time_limit_s / 60)} min · {t.takers} {t.takers === 1 ? "player" : "players"}
      </p>
      {a?.status === "finished" ? (
        <div className="tier-result">
          <div>
            <span className="big-number">
              {a.score}/{a.total}
            </span>
            <span className="small muted"> in {clockText(a.time_ms)}</span>
          </div>
          <p className="small">
            Rank #{a.rank} of {a.takers} · Top {a.top_percent}%
          </p>
          <div className="tier-actions">
            <Link to={`/ranked/${t.id}/result`}>Review</Link>
            <Link to={`/ranked/${t.id}/board`} className="primary">
              Leaderboard →
            </Link>
          </div>
        </div>
      ) : a?.status === "in_progress" ? (
        <div className="tier-actions">
          <Link to={`/ranked/${t.id}/play`} className="primary full">
            Resume · {clockText(a.remaining_ms)} left →
          </Link>
        </div>
      ) : confirming ? (
        <div className="confirm-start" role="alert">
          <p>
            <strong>You get one attempt.</strong> The clock starts now and keeps running if you leave.
          </p>
          <div className="tier-actions">
            <button onClick={() => setConfirming(false)}>Not yet</button>
            <button className="primary" onClick={() => navigate(`/ranked/${t.id}/play`)}>
              Start the clock →
            </button>
          </div>
        </div>
      ) : (
        <div className="tier-actions">
          <Link to={`/ranked/${t.id}/board`}>Leaderboard</Link>
          <button className="primary" disabled={!canStart} onClick={() => setConfirming(true)}>
            Take test
          </button>
        </div>
      )}
    </article>
  );
}

export function RankedPlay() {
  const tier = tierParam(useParams().tier);
  const navigate = useNavigate();
  const [session, setSession] = useState<RankedSession>();
  const [error, setError] = useState<unknown>();
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let active = true;
    setError(undefined);
    api
      .startRanked(tier)
      .then((s) => active && setSession(s))
      .catch((err) => {
        if (!active) return;
        if (err instanceof ApiError && err.code === "already_taken") navigate(`/ranked/${tier}/result`, { replace: true });
        else setError(err);
      });
    return () => {
      active = false;
    };
  }, [tier, version]);
  if (error) return <ErrorNotice error={error} retry={() => setVersion((v) => v + 1)} />;
  if (!session) return <Loading />;
  return <Player tier={tier} initial={session} />;
}

function Player({ tier, initial }: { tier: TierId; initial: RankedSession }) {
  const navigate = useNavigate();
  const deadline = useRef(Date.now() + initial.remaining_ms);
  const [answered, setAnswered] = useState(initial.answered);
  const [value, setValue] = useState<ResponseValue>();
  const [left, setLeft] = useState(initial.remaining_ms);
  const [busy, setBusy] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [confirmFinish, setConfirmFinish] = useState(false);
  const [error, setError] = useState<unknown>();
  const index = initial.questions.findIndex((q) => !(q.id in answered));
  const q = index >= 0 ? initial.questions[index] : undefined;
  const count = Object.keys(answered).length;

  async function finish() {
    if (finishing) return;
    setFinishing(true);
    setError(undefined);
    try {
      const result = await api.submitRanked(tier);
      navigate(`/ranked/${tier}/result`, { replace: true, state: result });
    } catch (err) {
      setError(err);
      setFinishing(false);
    }
  }

  useEffect(() => {
    const id = setInterval(() => {
      const ms = deadline.current - Date.now();
      setLeft(ms);
      if (ms <= 0) {
        clearInterval(id);
        void finish();
      }
    }, 250);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!q && !finishing) void finish();
  }, [q]);

  async function save() {
    if (!q || value === undefined || busy) return;
    setBusy(true);
    setError(undefined);
    try {
      const r = await api.answerRanked(tier, q.id, value);
      deadline.current = Date.now() + r.remaining_ms;
      setAnswered((a) => ({ ...a, [q.id]: value }));
      setValue(undefined);
      window.scrollTo({ top: 0 });
    } catch (err) {
      if (err instanceof ApiError && err.code === "already_answered") {
        setAnswered((a) => ({ ...a, [q.id]: value }));
        setValue(undefined);
      } else if (err instanceof ApiError && err.code === "time_up") {
        void finish();
      } else setError(err);
    } finally {
      setBusy(false);
    }
  }

  const urgent = left < 60_000;
  return (
    <section className="ranked-play">
      <div className="ranked-bar">
        <span className="eyebrow">{initial.title.toUpperCase()} · RANKED</span>
        <span className={`timer ${urgent ? "urgent" : ""}`} role="timer" aria-live={urgent ? "polite" : "off"}>
          ⏱ {clockText(left)}
        </span>
      </div>
      <div className="progress-dots" aria-label={`${count} of ${initial.total} answered`}>
        {initial.questions.map((qq, i) => (
          <span key={qq.id} className={qq.id in answered ? "done" : i === index ? "current" : ""} />
        ))}
      </div>
      {q && !finishing ? (
        <>
          <p className="small muted">
            Question {index + 1} of {initial.total} · answers are final, results at the end
          </p>
          <Question key={q.id} question={q} value={value} onChange={setValue} disabled={busy} />
          <button className="primary full" disabled={busy || !isComplete(q, value)} onClick={save}>
            {busy ? "Saving…" : index === initial.total - 1 ? "Save and finish →" : "Save answer →"}
          </button>
          {confirmFinish ? (
            <div className="confirm-start" role="alert">
              <p>Finish now? Unanswered questions count as wrong.</p>
              <div className="tier-actions">
                <button onClick={() => setConfirmFinish(false)}>Keep going</button>
                <button className="primary" onClick={finish}>
                  Finish test
                </button>
              </div>
            </div>
          ) : (
            <button className="text-button" onClick={() => setConfirmFinish(true)}>
              Finish early
            </button>
          )}
        </>
      ) : (
        <Loading />
      )}
      {!!error && <ErrorNotice error={error} retry={q ? save : finish} />}
    </section>
  );
}

export function RankedResultScreen() {
  const tier = tierParam(useParams().tier);
  const resource = useResource(() => api.getRankedResult(tier));
  return <Resource resource={resource}>{(r) => <ResultView result={r} />}</Resource>;
}

function answerText(r: RankedResult["review"][number], value: ResponseValue | null) {
  if (value === null || value === undefined) return "No answer";
  const q = r.question;
  if (Array.isArray(value)) return value.map((id) => q.options?.find((o) => o.id === id)?.text ?? id).join(" → ");
  if (q.format === "tap_line") return `Line ${value}`;
  return q.options?.find((o) => o.id === value)?.text ?? q.diagram?.nodes.find((n) => n.id === value)?.label ?? String(value);
}

function ResultView({ result: r }: { result: RankedResult }) {
  return (
    <section className="ranked-result">
      <p className="eyebrow">{r.title.toUpperCase()} · FINAL RESULT</p>
      <h1>
        {r.score}/{r.total}
        <span className="muted result-time"> in {clockText(r.time_ms)}</span>
      </h1>
      <div className="card standing">
        <div>
          <span className="big-number">#{r.rank}</span>
          <span className="small muted"> of {r.takers}</span>
        </div>
        <p>
          <strong>Top {r.top_percent}%</strong> of everyone who took the {r.title} test.
        </p>
        <Link to={`/ranked/${r.tier}/board`} className="primary full">
          See the leaderboard →
        </Link>
      </div>
      <h2>Review</h2>
      {r.review.length === 0 && <p>No answers were recorded for this attempt.</p>}
      <ol className="review-list">
        {r.review.map((item, i) => (
          <li key={item.question.id} className={`card review-item ${item.correct ? "correct" : "incorrect"}`}>
            <div className="split">
              <span className="eyebrow">QUESTION {i + 1}</span>
              <span className="pill">{item.correct ? "✓ CORRECT" : "✗ MISSED"}</span>
            </div>
            <p className="review-prompt">
              <Rich text={item.question.prompt} />
            </p>
            {item.question.code && <pre className="code example-code">{item.question.code}</pre>}
            {!item.correct && (
              <p className="small">
                <strong>Your answer:</strong> {answerText(item, item.response)}
              </p>
            )}
            <p className="small">
              <strong>Correct:</strong> {answerText(item, item.correct_answer)}
            </p>
            <p className="small">
              <Rich text={item.explanation} />
            </p>
          </li>
        ))}
      </ol>
      <Link to="/ranked" className="back-link">
        ← All ranked tests
      </Link>
    </section>
  );
}

export function LeaderboardScreen() {
  const tier = tierParam(useParams().tier);
  const resource = useResource(() => api.getLeaderboard(tier));
  return (
    <Resource resource={resource}>
      {(b) => (
        <section className="leaderboard">
          <Link to="/ranked" className="back-link">
            ← Ranked
          </Link>
          <p className="eyebrow">LEADERBOARD</p>
          <h1>{b.title}</h1>
          <p className="intro">
            {b.takers} {b.takers === 1 ? "player" : "players"}. Most correct wins; ties go to the faster time.
          </p>
          {b.you && (
            <div className="card you-row">
              <span>
                You: <strong>#{b.you.rank}</strong> · {b.you.score}/{b.you.total} in {clockText(b.you.time_ms)}
              </span>
              <span className="pill">TOP {b.you.top_percent}%</span>
            </div>
          )}
          <ol className="board card">
            {b.top.map((e) => (
              <li key={e.rank} className={e.you ? "you" : ""}>
                <span className="board-rank">{e.rank}</span>
                <span className="board-name">
                  {e.username}
                  {e.sample && <span className="sample-tag">sample</span>}
                  {e.you && <span className="sample-tag you-tag">you</span>}
                </span>
                <span className="board-score">
                  {e.score}/{e.total}
                </span>
                <span className="board-time">{clockText(e.time_ms)}</span>
              </li>
            ))}
          </ol>
          {b.top.some((e) => e.sample) && (
            <p className="small muted">Entries tagged "sample" are generated demo players, not real people.</p>
          )}
        </section>
      )}
    </Resource>
  );
}
