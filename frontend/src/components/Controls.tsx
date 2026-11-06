import clsx from "clsx";
import { useApp } from "../lib/store";

const SPEEDS = [1, 2, 4, 8, 16, 32] as const;

export function Controls({ onSeek }: { onSeek: (idx: number) => void }) {
  const { playing, setPlaying, speed, setSpeed, meta, frame } = useApp();
  const totalWindows = meta?.n_windows ?? 0;
  const currentIdx = frame?.i ?? 0;
  const pct = totalWindows > 0 ? (currentIdx / (totalWindows - 1)) * 100 : 0;
  const duration = meta?.meta?.duration_s ?? 0;
  const currentT = frame?.t1 ?? 0;

  return (
    <section className="panel">
      <div className="p-3 flex items-center gap-4">
        {/* Play / pause */}
        <button
          onClick={() => setPlaying(!playing)}
          className={clsx(
            "w-11 h-11 rounded-full flex items-center justify-center transition",
            "border-2 border-signal-green bg-signal-green/10 hover:bg-signal-green/20",
            "shadow-glow shadow-signal-green/30",
          )}
          aria-label={playing ? "Pause" : "Play"}
        >
          {playing ? (
            <svg viewBox="0 0 24 24" width="18" height="18" fill="#22d3a0">
              <rect x="6" y="5" width="4" height="14" rx="1" />
              <rect x="14" y="5" width="4" height="14" rx="1" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" width="18" height="18" fill="#22d3a0">
              <path d="M7 5l12 7-12 7z" />
            </svg>
          )}
        </button>

        {/* Scrub bar */}
        <div className="flex-1 flex items-center gap-3">
          <span className="mono text-xs text-slate-400 w-16 text-right">
            {currentT.toFixed(1)}s
          </span>
          <div className="flex-1 relative h-8 flex items-center">
            <input
              type="range"
              min={0}
              max={Math.max(0, totalWindows - 1)}
              value={currentIdx}
              onChange={(e) => onSeek(parseInt(e.target.value, 10))}
              className="w-full h-1.5 bg-ink-700 rounded-full appearance-none cursor-pointer
                         accent-signal-green"
              style={{
                background: `linear-gradient(to right,
                  #22d3a0 0%, #22d3a0 ${pct}%,
                  #1a2238 ${pct}%, #1a2238 100%)`,
              }}
            />
          </div>
          <span className="mono text-xs text-slate-500 w-16">
            / {duration.toFixed(1)}s
          </span>
        </div>

        {/* Speed */}
        <div className="flex items-center gap-1 pl-3 border-l border-ink-700">
          <span className="text-[10px] mono text-slate-500 mr-1 uppercase tracking-wider">
            Speed
          </span>
          {SPEEDS.map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className={clsx(
                "px-2 py-1 mono text-xs rounded transition",
                speed === s
                  ? "bg-signal-green/20 text-signal-green border border-signal-green/40"
                  : "text-slate-500 hover:text-slate-300 border border-transparent",
              )}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
