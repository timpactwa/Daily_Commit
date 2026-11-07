import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError, getUserId } from "../api";
import { Resource, useResource } from "../ui";

export function Account() {
  const resource = useResource(async () => (getUserId() ? api.getMe().catch(() => null) : null));
  return (
    <section className="account onboarding">
      <p className="eyebrow">ACCOUNT</p>
      <Resource resource={resource}>
        {(me) =>
          me?.has_account ? (
            <SignedIn username={me.username ?? me.display_name} />
          ) : (
            <AuthForm hasGuest={!!me && me.user_id !== "demo"} />
          )
        }
      </Resource>
    </section>
  );
}

function SignedIn({ username }: { username: string }) {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  return (
    <>
      <h1>
        Signed in as {username}
        <span className="green">.</span>
      </h1>
      <div className="card">
        <p>Your streak, ratings, guides and ranked results are saved to this account. Sign in on any device to pick up where you left off.</p>
        <Link to="/ranked" className="primary full">
          Go to ranked tests →
        </Link>
        <button
          className="full"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            await api.logout().catch(() => undefined);
            navigate("/onboarding", { replace: true });
          }}
        >
          Sign out
        </button>
      </div>
    </>
  );
}

function AuthForm({ hasGuest }: { hasGuest: boolean }) {
  const [mode, setMode] = useState<"signup" | "login">(hasGuest ? "signup" : "login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const navigate = useNavigate();

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(undefined);
    try {
      const r = mode === "signup" ? await api.signup(username, password) : await api.login(username, password);
      navigate(r.user.placed ? "/" : "/placement", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError || err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1>
        {mode === "signup" ? "Save your progress" : "Welcome back"}
        <span className="green">.</span>
      </h1>
      <p>
        {mode === "signup"
          ? hasGuest
            ? "Pick a username. Everything you've done so far comes with you, and you can take ranked tests."
            : "Pick a username to save your progress and take ranked tests."
          : "Sign in to pick up your streak and ranked results."}
      </p>
      <div className="card">
        <form onSubmit={submit}>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            autoComplete="username"
            autoCapitalize="none"
            spellCheck={false}
            minLength={3}
            maxLength={20}
            pattern="[A-Za-z0-9_]{3,20}"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="letters, numbers, _"
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete={mode === "signup" ? "new-password" : "current-password"}
            minLength={mode === "signup" ? 8 : 1}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={mode === "signup" ? "at least 8 characters" : ""}
          />
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <button className="primary full" disabled={busy}>
            {busy ? "One moment…" : mode === "signup" ? "Create account →" : "Sign in →"}
          </button>
        </form>
        <button className="text-button" onClick={() => { setMode(mode === "signup" ? "login" : "signup"); setError(undefined); }}>
          {mode === "signup" ? "Already have an account? Sign in" : "New here? Create an account"}
        </button>
      </div>
    </>
  );
}
