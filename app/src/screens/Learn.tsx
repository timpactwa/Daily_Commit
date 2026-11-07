import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, type LearnCheckResult, type LearnModule, type LearnSection } from "../api";
import { buzz, ErrorNotice, Resource, Rich, useResource } from "../ui";

const TRACKS = [
  { id: "system-design", label: "◇ SYSTEM DESIGN" },
  { id: "debugging", label: "⌘ DEBUGGING" },
] as const;

export function LearnList() {
  const resource = useResource(api.getModules);
  return (
    <section className="learn">
      <p className="eyebrow">LEARN</p>
      <h1>
        Read it. Check it. Own it<span className="green">.</span>
      </h1>
      <p className="intro">
        Short guides for every topic, with worked examples and a quick check after each part.
      </p>
      <Resource resource={resource}>
        {({ modules }) => (
          <>
            {TRACKS.map((track) => (
              <section className="track-section" key={track.id}>
                <p className="eyebrow">{track.label}</p>
                <div className="module-grid">
                  {modules
                    .filter((m) => m.track === track.id)
                    .map((m) => (
                      <Link to={`/learn/${m.topic}`} className="card module-card" key={m.topic}>
                        <div className="split">
                          <strong>{m.title}</strong>
                          {m.completed ? (
                            <span className="pill learned">✓ LEARNED</span>
                          ) : (
                            <span className="pill">{m.minutes} MIN</span>
                          )}
                        </div>
                        <p>{m.summary}</p>
                        <div className="module-meter" aria-label={`${m.passed} of ${m.sections} parts done`}>
                          {Array.from({ length: m.sections }, (_, i) => (
                            <span key={i} className={i < m.passed ? "on" : ""} />
                          ))}
                        </div>
                      </Link>
                    ))}
                </div>
              </section>
            ))}
            {modules.length === 0 && (
              <div className="card">
                <p>Guides are on their way.</p>
              </div>
            )}
          </>
        )}
      </Resource>
    </section>
  );
}

export function LearnModuleScreen() {
  const { topic = "" } = useParams();
  const resource = useResource(() => api.getModule(topic));
  return <Resource resource={resource}>{(m) => <ModuleReader key={m.topic} module={m} />}</Resource>;
}

function ModuleReader({ module: m }: { module: LearnModule }) {
  const [passed, setPassed] = useState<string[]>(m.progress.passed);
  const unlocked = Math.min(m.sections.length, passed.length + 1);
  const completed = passed.length === m.sections.length;
  return (
    <article className="module">
      <Link to="/learn" className="back-link">
        ← All guides
      </Link>
      <p className="eyebrow">
        {m.track === "debugging" ? "⌘ DEBUGGING" : "◇ SYSTEM DESIGN"} · {m.minutes} MIN READ
      </p>
      <h1>{m.title}</h1>
      <p className="intro">{m.summary}</p>
      {m.sections.slice(0, unlocked).map((s, i) => (
        <Section
          key={s.id}
          topic={m.topic}
          section={s}
          index={i}
          alreadyPassed={passed.includes(s.id)}
          onPassed={(r) => setPassed(r.passed)}
        />
      ))}
      {!completed && unlocked < m.sections.length && (
        <p className="locked-note">
          🔒 {m.sections.length - unlocked} more {m.sections.length - unlocked === 1 ? "part unlocks" : "parts unlock"} as you answer
          each check.
        </p>
      )}
      {completed && (
        <div className="card module-done">
          <p className="eyebrow">GUIDE COMPLETE</p>
          <h2>You learned {m.title}.</h2>
          <p>Your daily practice will keep testing it. Ready to put it to work?</p>
          <Link to="/lesson" className="primary full">
            Practice today's commit →
          </Link>
        </div>
      )}
      <footer className="sources">
        <p className="eyebrow">SOURCES</p>
        <ol>
          {m.sources.map((src) => (
            <li key={src.url}>
              <a href={src.url} target="_blank" rel="noreferrer noopener">
                {src.title}
              </a>
              <span className="muted">, {src.publisher}</span>
            </li>
          ))}
        </ol>
      </footer>
    </article>
  );
}

function Section({
  topic,
  section: s,
  index,
  alreadyPassed,
  onPassed,
}: {
  topic: string;
  section: LearnSection;
  index: number;
  alreadyPassed: boolean;
  onPassed: (r: LearnCheckResult) => void;
}) {
  const [choice, setChoice] = useState<string>();
  const [result, setResult] = useState<LearnCheckResult>();
  const [wrong, setWrong] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>();
  const done = alreadyPassed || !!result?.correct;

  async function check() {
    if (!choice || busy) return;
    setBusy(true);
    setError(undefined);
    try {
      const r = await api.checkSection(topic, s.id, choice);
      setResult(r);
      if (r.correct) onPassed(r);
      else {
        setWrong((w) => [...w, choice]);
        setChoice(undefined);
      }
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card module-section">
      <p className="eyebrow">PART {index + 1}</p>
      <h2>{s.heading}</h2>
      {s.body.map((para, i) => (
        <p key={i}>
          <Rich text={para} />
        </p>
      ))}
      <div className="example">
        <p className="eyebrow">EXAMPLE · {s.example.title.toUpperCase()}</p>
        {s.example.code && <pre className="code example-code">{s.example.code}</pre>}
        {s.example.text && (
          <p>
            <Rich text={s.example.text} />
          </p>
        )}
      </div>
      <div className={`checkpoint ${done ? "passed" : ""}`}>
        <p className="eyebrow">{done ? "✓ CHECK PASSED" : "QUICK CHECK"}</p>
        <h3>
          <Rich text={s.check.prompt} />
        </h3>
        {!done && (
          <>
            <div className="options">
              {s.check.options.map((o, i) => (
                <button
                  key={o.id}
                  className={`option ${choice === o.id ? "selected" : ""} ${wrong.includes(o.id) ? "ruled-out" : ""}`}
                  aria-pressed={choice === o.id}
                  disabled={busy || wrong.includes(o.id)}
                  onClick={() => {
                    buzz();
                    setChoice(o.id);
                    setResult(undefined);
                  }}
                >
                  <span className="option-key">{String.fromCharCode(65 + i)}</span>
                  <Rich text={o.text} />
                </button>
              ))}
            </div>
            {result && !result.correct && (
              <p className="retry-note" role="status">
                Not quite. Reread the part above and try again.
              </p>
            )}
            <button className="primary full" disabled={!choice || busy} onClick={check}>
              {busy ? "Checking…" : "Check answer"}
            </button>
          </>
        )}
        {result?.correct && result.explanation && (
          <p className="check-explanation" role="status">
            <Rich text={result.explanation} />
          </p>
        )}
        {!!error && <ErrorNotice error={error} retry={check} />}
      </div>
    </section>
  );
}
