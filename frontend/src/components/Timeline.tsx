import { useApp } from "../lib/store";
import { CLASS_COLORS, CLASS_NAMES } from "../lib/types";

// Full-recording timeline showing the ground-truth regime schedule plus a
// live cursor and a running tape of predicted states.

export function Timeline() {
  const { meta, frame } = useApp();
  if (!meta) {
    return (
      <section className="panel">
        <div className="panel-header"><span>Recording Timeline</span></div>
        <div className="p-4 text-sm text-slate-500">Select a recording to begin.</div>
      </section>
    );
  }
  const duration = meta.meta.duration_s;
  const cursor = frame ? (frame.t1 / duration) * 100 : 0;

  return (
    <section className="panel">
      <div className="panel-header">
        <span>Recording Timeline</span>
        <span className="mono text-[10px] text-slate-500 normal-case">
          {meta.meta.label}
        </span>
      </div>
      <div className="p-4">
        <div className="text-[10px] mono tracking-wider text-slate-500 uppercase mb-1">
          Ground truth schedule
        </div>
        <div className="relative h-6 rounded overflow-hidden border border-ink-700/60">
          {meta.meta.schedule.map((s, idx) => {
            const left = (s.start_s / duration) * 100;
            const width = ((s.end_s - s.start_s) / duration) * 100;
            const color = CLASS_COLORS[s.regime];
            return (
              <div
                key={idx}
                className="absolute inset-y-0"
                style={{ left: `${left}%`, width: `${width}%`,
                         background: `${color}80` }}
                title={`${s.regime} ${s.start_s}-${s.end_s}s`}
              />
            );
          })}
          {/* Cursor */}
          {frame && (
            <div
              className="absolute inset-y-0 w-0.5 bg-white shadow-glow shadow-white/50"
              style={{ left: `${cursor}%` }}
            />
          )}
        </div>
        <div className="flex items-center justify-between mt-1 text-[10px] mono text-slate-500">
          <span>0 s</span>
          <span>{(duration / 2).toFixed(0)} s</span>
          <span>{duration.toFixed(0)} s</span>
        </div>

        <div className="mt-4 flex items-center gap-4 text-[10px] mono uppercase tracking-wider">
          {CLASS_NAMES.map((n) => (
            <div key={n} className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm" style={{ background: CLASS_COLORS[n] }} />
              <span className="text-slate-400">{n}</span>
            </div>
          ))}
        </div>

        <p className="mt-3 text-xs text-slate-500 leading-relaxed">
          {meta.meta.description}
        </p>
      </div>
    </section>
  );
}
