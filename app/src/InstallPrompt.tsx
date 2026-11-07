import { useEffect, useState } from "react";
interface InstallEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: string }>;
}
export function InstallPrompt() {
  const [prompt, setPrompt] = useState<InstallEvent>();
  const [dismissed, setDismissed] = useState(false);
  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setPrompt(e as InstallEvent);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);
  if (!prompt || dismissed) return null;
  return (
    <aside className="install-prompt">
      <span>Make a little space for your daily habit.</span>
      <button
        onClick={async () => {
          await prompt.prompt();
          await prompt.userChoice;
          setPrompt(undefined);
        }}
      >
        Install app
      </button>
      <button
        className="quiet"
        aria-label="Dismiss install prompt"
        onClick={() => setDismissed(true)}
      >
        ×
      </button>
    </aside>
  );
}
