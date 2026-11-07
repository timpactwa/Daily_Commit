import { useState, type FormEvent } from "react";
import {
  Link,
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { api } from "./api";
import { Lesson } from "./screens/Lesson";
import { Placement, PlacementResult } from "./screens/Placement";
import { ErrorNotice } from "./ui";
import { Logo } from "./Logo";
import { InstallPrompt } from "./InstallPrompt";
import { Home, Progress, LessonDone, Tomorrow } from "./screens/Dashboard";
function Onboarding() {
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>();
  const navigate = useNavigate();
  async function submit(event?: FormEvent) {
    event?.preventDefault();
    if (!name.trim() || busy) return;
    setBusy(true);
    setError(undefined);
    try {
      await api.createUser(name.trim());
      navigate("/placement");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="onboarding">
      <p className="eyebrow">FIVE MINUTES. FOR YOUR FUTURE.</p>
      <h1>
        Small commits.
        <br />
        Real progress<span className="green">.</span>
      </h1>
      <p>
        Build your interview instincts, one day at a time. System design and
        debugging practice that grows with you.
      </p>
      <div className="card">
        <h2>Make your first commit.</h2>
        <p>A quick placement finds your starting point. No prep needed.</p>
        <form onSubmit={submit}>
          <label htmlFor="name">What should we call you?</label>
          <input
            id="name"
            autoComplete="given-name"
            maxLength={60}
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your first name"
          />
          <button className="primary full" disabled={busy || !name.trim()}>
            {busy ? "Setting up…" : "Find my starting point →"}
          </button>
        </form>
        {!!error && <ErrorNotice error={error} retry={submit} />}
      </div>
    </div>
  );
}
export function App() {
  const location = useLocation();
  return (
    <div className="app">
      <header>
        <Logo />
        <span className="eyebrow">A LITTLE, EVERY DAY</span>
      </header>
      <InstallPrompt />
      <main>
        <Routes key={location.key}>
          <Route path="/" element={<Home />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/lesson" element={<Lesson />} />
          <Route path="/placement" element={<Placement />} />
          <Route path="/placement/result" element={<PlacementResult />} />
          <Route path="/lesson/done" element={<LessonDone />} />
          <Route path="/progress" element={<Progress />} />
          <Route path="/tomorrow" element={<Tomorrow />} />
          <Route
            path="*"
            element={
              <div className="card">
                <h1>Wrong turn.</h1>
                <Link to="/">Back to today →</Link>
              </div>
            }
          />
        </Routes>
      </main>
      <nav aria-label="Main navigation">
        <NavLink to="/" end>
          ⌂ <span>Today</span>
        </NavLink>
        <NavLink to="/progress">
          ↗ <span>Progress</span>
        </NavLink>
      </nav>
    </div>
  );
}
