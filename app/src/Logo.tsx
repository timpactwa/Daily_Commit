import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "./api";
import { buzz, ErrorNotice } from "./ui";
export function Logo() {
  const navigate = useNavigate();
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const held = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>();
  function cancel() {
    if (timer.current) clearTimeout(timer.current);
    timer.current = undefined;
  }
  useEffect(() => cancel, []);
  async function switchUser() {
    setBusy(true);
    setError(undefined);
    try {
      await api.demoSwitch();
      buzz();
      navigate("/", { replace: true, state: { switched: Date.now() } });
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }
  function start() {
    if (busy) return;
    held.current = false;
    cancel();
    timer.current = setTimeout(() => {
      held.current = true;
      void switchUser();
    }, 1000);
  }
  return (
    <>
      <button
        className="brand logo-button"
        disabled={busy}
        aria-label="Daily Commit home. Hold for one second to switch to the demo user."
        onPointerDown={start}
        onPointerUp={cancel}
        onPointerCancel={cancel}
        onPointerLeave={cancel}
        onContextMenu={(e) => e.preventDefault()}
        onKeyDown={(e) => {
          if ((e.key === " " || e.key === "Enter") && !e.repeat) start();
        }}
        onKeyUp={cancel}
        onBlur={cancel}
        onClick={() => {
          if (!held.current) navigate("/");
          held.current = false;
        }}
      >
        [d<span>c</span>]{" "}
        <strong>
          daily commit<span className="brand-dot">.</span>
        </strong>
      </button>
      {!!error && (
        <div className="logo-error">
          <ErrorNotice error={error} retry={switchUser} />
          <button onClick={() => setError(undefined)}>Dismiss</button>
        </div>
      )}
    </>
  );
}
