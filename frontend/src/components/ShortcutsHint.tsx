import { useEffect, useState } from "react";

const SHORTCUTS: Array<[string, string]> = [
  ["Space", "Play / pause"],
  ["← / →", "Seek ± 5 windows"],
  ["1 … 6", "Speed 1x … 32x"],
  ["?", "Toggle this panel"],
];

export function ShortcutsHint() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "?" || (e.key === "/" && e.shiftKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/70 backdrop-blur-sm"
      onClick={() => setOpen(false)}
    >
      <div
        className="panel max-w-md w-[90vw]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="panel-header">
          <span>Keyboard Shortcuts</span>
          <button
            onClick={() => setOpen(false)}
            className="text-slate-500 hover:text-slate-200 transition"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <div className="p-5 space-y-3">
          {SHORTCUTS.map(([keys, label]) => (
            <div key={keys} className="flex items-center justify-between">
              <span className="text-sm text-slate-300">{label}</span>
              <kbd className="mono text-xs px-2 py-1 bg-ink-800 border border-ink-700 rounded">
                {keys}
              </kbd>
            </div>
          ))}
          <div className="pt-3 border-t border-ink-700/50 text-xs text-slate-500 text-center">
            Press <kbd className="mono px-1 bg-ink-800 border border-ink-700 rounded">Esc</kbd> to close
          </div>
        </div>
      </div>
    </div>
  );
}
