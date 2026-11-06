import { useApp } from "../lib/store";
import { CLASS_LABELS, CLASS_NAMES, CLASS_COLORS } from "../lib/types";

export function MetricsPanel() {
  const metrics = useApp((s) => s.metrics);
  if (!metrics) {
    return (
      <section className="panel">
        <div className="panel-header"><span>Model Performance</span></div>
        <div className="p-6 text-slate-500 text-sm">Loading metrics…</div>
      </section>
    );
  }
  const h = metrics.hybrid.test;
  const b = metrics.baseline.test;
  const cm = h.confusion_matrix ?? [[0,0,0],[0,0,0],[0,0,0]];

  return (
    <section className="panel">
      <div className="panel-header">
        <span>Model Performance</span>
        <span className="mono text-[10px] text-slate-500 normal-case">
          Held-out test set · n=504
        </span>
      </div>
      <div className="p-4 grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiTile label="Accuracy" value={h.accuracy * 100} suffix="%"
          delta={(h.accuracy - b.accuracy) * 100} />
        <KpiTile label="Macro F1" value={h.macro_f1} precision={3}
          delta={h.macro_f1 - b.macro_f1} />
        <KpiTile label="Preictal AUC" value={h.auc_per_class.preictal} precision={3} />
        <KpiTile label="Ictal AUC" value={h.auc_per_class.ictal} precision={3} />
      </div>

      <div className="px-4 pb-4 grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Confusion matrix */}
        <div className="lg:col-span-3 rounded-md bg-ink-800/40 border border-ink-700/40 p-3">
          <div className="text-[10px] mono tracking-wider text-slate-500 uppercase mb-2">
            Confusion matrix (hybrid)
          </div>
          <ConfusionMatrix cm={cm as number[][]} />
        </div>

        {/* Ablation */}
        <div className="lg:col-span-2 rounded-md bg-ink-800/40 border border-ink-700/40 p-3">
          <div className="text-[10px] mono tracking-wider text-slate-500 uppercase mb-2">
            Ablation · hybrid vs baseline
          </div>
          <div className="space-y-2 text-sm">
            <KpiRow label="Accuracy" a={h.accuracy} b={b.accuracy} />
            <KpiRow label="Macro F1" a={h.macro_f1} b={b.macro_f1} />
            <KpiRow label="Preictal AUC" a={h.auc_per_class.preictal} b={b.auc_per_class.preictal} />
            <KpiRow label="Ictal AUC" a={h.auc_per_class.ictal} b={b.auc_per_class.ictal} />
          </div>
          <div className="mt-3 pt-3 border-t border-ink-700/40 text-xs text-slate-400 leading-relaxed">
            Hybrid adds interpretable 6-D Jansen-Rit state.
            {" "}Baseline is identical TCN with PINN head removed.
          </div>
        </div>
      </div>
    </section>
  );
}

function KpiTile({ label, value, precision = 2, suffix = "", delta }: {
  label: string; value: number; precision?: number; suffix?: string; delta?: number;
}) {
  return (
    <div className="rounded-md bg-ink-800/40 border border-ink-700/40 p-3">
      <div className="text-[10px] mono tracking-wider text-slate-500 uppercase">{label}</div>
      <div className="flex items-baseline gap-2 mt-1">
        <span className="mono text-xl font-semibold text-slate-100">
          {value.toFixed(precision)}{suffix}
        </span>
        {delta !== undefined && (
          <span className={`mono text-[10px] ${delta > 0 ? "text-signal-green" : delta < 0 ? "text-signal-red" : "text-slate-500"}`}>
            {delta > 0 ? "▲" : delta < 0 ? "▼" : "—"} {Math.abs(delta).toFixed(precision)}
          </span>
        )}
      </div>
    </div>
  );
}

function KpiRow({ label, a, b }: { label: string; a: number; b: number }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-slate-400 text-xs">{label}</span>
      <div className="flex items-center gap-2 mono text-xs">
        <span className="text-slate-100">{a.toFixed(3)}</span>
        <span className="text-slate-600">vs</span>
        <span className="text-slate-500">{b.toFixed(3)}</span>
      </div>
    </div>
  );
}

function ConfusionMatrix({ cm }: { cm: number[][] }) {
  const max = Math.max(...cm.flat(), 1);
  return (
    <div className="flex items-start gap-2">
      <div className="flex flex-col justify-center text-[9px] mono text-slate-500 uppercase pt-5">
        <span style={{ writingMode: "vertical-rl" }} className="rotate-180">True</span>
      </div>
      <div className="flex-1">
        <div className="grid grid-cols-[auto_1fr_1fr_1fr] gap-1 items-center">
          <div />
          {CLASS_NAMES.map((n) => (
            <div key={n} className="text-center text-[9px] mono uppercase tracking-wider"
                 style={{ color: CLASS_COLORS[n] }}>{n.slice(0, 3)}</div>
          ))}
          {cm.map((row, i) => (
            <div key={i} className="contents">
              <div className="text-[9px] mono uppercase text-slate-500 text-right pr-1"
                   style={{ color: CLASS_COLORS[CLASS_NAMES[i]] }}>
                {CLASS_NAMES[i].slice(0, 3)}
              </div>
              {row.map((v, j) => {
                const intensity = v / max;
                const isDiag = i === j;
                const bg = isDiag
                  ? `rgba(34,211,160,${0.1 + 0.5 * intensity})`
                  : v === 0
                    ? "rgba(26,34,56,0.4)"
                    : `rgba(255,51,96,${0.15 + 0.4 * intensity})`;
                return (
                  <div
                    key={j}
                    className="aspect-square rounded flex items-center justify-center text-sm font-semibold mono"
                    style={{ background: bg, color: v === 0 ? "#30406a" : "#d7deeb" }}
                  >
                    {v}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
        <div className="text-center text-[9px] mono text-slate-500 uppercase mt-1">Predicted</div>
      </div>
    </div>
  );
}
