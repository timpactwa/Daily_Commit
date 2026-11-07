import { useEffect, useState, type FormEvent } from "react";
import {
  Link,
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { api, getToken, type Features } from "./api";
import { Lesson } from "./screens/Lesson";
import { Placement, PlacementResult } from "./screens/Placement";
import { ErrorNotice } from "./ui";
import { Logo } from "./Logo";
import { InstallPrompt } from "./InstallPrompt";
import { Backdrop } from "./Backdrop";
import { Home, Progress, LessonDone, Tomorrow } from "./screens/Dashboard";
import { LearnList, LearnModuleScreen } from "./screens/Learn";
import { LeaderboardScreen, RankedHome, RankedPlay, RankedResultScreen } from "./screens/Ranked";
import { Account } from "./screens/Account";

const ALL_OFF: Features = { learn: false, ranked: false, accounts: false };

function useFeatures() {
  const [features, setFeatures] = useState<Features>(ALL_OFF);
  useEffect(() => {
    void api.getConfig().then(setFeatures);
  }, []);
  return features;
}
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
        <Link to="/account" className="text-button">
          Already have an account? Sign in
        </Link>
      </div>
    </div>
  );
}
export function App() {
  const location = useLocation();
  const features = useFeatures();
  return (
    <>
    <Backdrop />
    <div className="app">
      <header>
        <Logo />
        {features.accounts ? (
          <Link to="/account" className="account-link" aria-label="Account">
            {getToken() ? "◉ Account" : "○ Sign in"}
          </Link>
        ) : (
          <span className="eyebrow">A LITTLE, EVERY DAY</span>
        )}
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
          {features.learn && <Route path="/learn" element={<LearnList />} />}
          {features.learn && <Route path="/learn/:topic" element={<LearnModuleScreen />} />}
          {features.ranked && <Route path="/ranked" element={<RankedHome />} />}
          {features.ranked && <Route path="/ranked/:tier/play" element={<RankedPlay />} />}
          {features.ranked && <Route path="/ranked/:tier/result" element={<RankedResultScreen />} />}
          {features.ranked && <Route path="/ranked/:tier/board" element={<LeaderboardScreen />} />}
          {features.accounts && <Route path="/account" element={<Account />} />}
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
        {features.learn && (
          <NavLink to="/learn">
            ❏ <span>Learn</span>
          </NavLink>
        )}
        {features.ranked && (
          <NavLink to="/ranked">
            ◆ <span>Ranked</span>
          </NavLink>
        )}
        <NavLink to="/progress">
          ↗ <span>Progress</span>
        </NavLink>
      </nav>
    </div>
    </>
  );
}
