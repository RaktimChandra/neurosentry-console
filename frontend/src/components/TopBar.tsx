import { useApp } from "../lib/store";

export function TopBar() {
  const { connected, wsError, meta, frame } = useApp();
  const latency = frame ? Math.round(frame.latency_ms) : null;
  return (
    <header className="relative flex items-center justify-between px-6 py-3 border-b border-ink-700/60 bg-ink-900/60 backdrop-blur-md z-10">
      <div className="absolute inset-x-0 top-0 h-[1px] scanline" aria-hidden />

      <div className="flex items-center gap-4">
        <div className="relative">
          <svg viewBox="0 0 64 64" width="34" height="34">
            <defs>
              <linearGradient id="hg" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#22d3a0" />
                <stop offset="100%" stopColor="#7dd3fc" />
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="60" height="60" rx="12" fill="#0a0e1a" stroke="url(#hg)" strokeWidth="2" />
            <path d="M8 34 L18 34 L22 22 L30 46 L38 18 L46 34 L56 34"
              fill="none" stroke="url(#hg)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div className="flex flex-col">
          <div className="flex items-baseline gap-3">
            <span className="text-[15px] font-semibold tracking-wide text-slate-100">
              NeuroSentry
            </span>
            <span className="text-[11px] mono text-slate-500 uppercase tracking-[0.2em]">
              Clinical Console
            </span>
          </div>
          <span className="text-[11px] text-slate-500">
            Physics-Informed Pre-Ictal EEG Forecasting
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {meta && (
          <div className="hidden md:flex items-center gap-2 pill">
            <span className="text-slate-400">Patient</span>
            <span className="text-slate-100">{meta.patient_id.toUpperCase()}</span>
          </div>
        )}
        {latency !== null && (
          <div className="hidden md:flex items-center gap-2 pill">
            <span className="text-slate-400">Inference</span>
            <span className="text-slate-100">{latency} ms</span>
          </div>
        )}
        <div className="pill" title={wsError ?? ""}>
          <span className={`led ${connected ? "led-green" : "led-red"}`} />
          <span>{connected ? "LIVE" : wsError ? "ERROR" : "OFFLINE"}</span>
        </div>
      </div>
    </header>
  );
}
