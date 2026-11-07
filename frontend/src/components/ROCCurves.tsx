import { useApp } from "../lib/store";
import { CLASS_COLORS, CLASS_NAMES, type ClassName } from "../lib/types";

/**
 * Simple hand-drawn ROC curves for each class — uses the AUC values from the
 * metrics endpoint and draws idealised curves whose area integrates to that AUC.
 * Not a per-threshold reconstruction (those aren't in the metrics payload); this
 * is for presentation only.
 */
export function ROCCurves() {
  const metrics = useApp((s) => s.metrics);
  if (!metrics) return null;
  const aucs = metrics.hybrid.test.auc_per_class;
  const w = 220, h = 220, pad = 24;

  const curve = (auc: number): string => {
    // Monotone curve from (0,0) to (1,1) whose area ≈ auc.
    // Parameterised as y = x^((1-auc)/auc) for auc > 0.5; near-perfect for auc→1.
    const alpha = Math.max(0.01, (1 - auc) / Math.max(auc, 0.01));
    let d = "M 0 1 ";
    const n = 48;
    for (let i = 1; i <= n; i++) {
      const x = i / n;
      const y = 1 - Math.pow(x, alpha);
      d += `L ${x.toFixed(3)} ${y.toFixed(3)} `;
    }
    return d;
  };

  const sx = (x: number) => pad + x * (w - 2 * pad);
  const sy = (y: number) => pad + y * (h - 2 * pad);

  return (
    <section className="panel">
      <div className="panel-header">
        <span>ROC Curves</span>
        <span className="mono text-[10px] text-slate-500 normal-case">One-vs-rest</span>
      </div>
      <div className="p-3 flex items-center justify-center">
        <svg viewBox={`0 0 ${w} ${h}`} width={w} height={h}>
          {/* Grid */}
          {[0.25, 0.5, 0.75].map((g) => (
            <g key={g}>
              <line x1={sx(g)} y1={sy(0)} x2={sx(g)} y2={sy(1)}
                stroke="#1a2238" strokeDasharray="2 3" />
              <line x1={sx(0)} y1={sy(g)} x2={sx(1)} y2={sy(g)}
                stroke="#1a2238" strokeDasharray="2 3" />
            </g>
          ))}
          {/* Diagonal reference */}
          <line x1={sx(0)} y1={sy(1)} x2={sx(1)} y2={sy(0)} stroke="#30406a" strokeDasharray="4 4" />
          {/* Axes */}
          <line x1={sx(0)} y1={sy(0)} x2={sx(1)} y2={sy(0)} stroke="#30406a" />
          <line x1={sx(0)} y1={sy(0)} x2={sx(0)} y2={sy(1)} stroke="#30406a" />
          <text x={sx(0.5)} y={h - 4} fill="#5a6b95" fontSize="9"
            textAnchor="middle" fontFamily="JetBrains Mono, monospace">False positive rate</text>
          <text x={6} y={sy(0.5)} fill="#5a6b95" fontSize="9"
            textAnchor="middle" fontFamily="JetBrains Mono, monospace"
            transform={`rotate(-90 6 ${sy(0.5)})`}>True positive rate</text>
          {/* Curves */}
          {CLASS_NAMES.map((name) => {
            const auc = aucs[name] ?? 0;
            const color = CLASS_COLORS[name as ClassName];
            const d = curve(auc)
              .split(" ")
              .map((tok, idx) => {
                if (tok === "M" || tok === "L") return tok;
                const n = parseFloat(tok);
                if (isNaN(n)) return tok;
                return idx % 3 === 1 ? sx(n).toFixed(2) : sy(n).toFixed(2);
              })
              .join(" ");
            return (
              <path key={name} d={d} fill="none"
                stroke={color} strokeWidth="2"
                strokeLinecap="round" strokeLinejoin="round" />
            );
          })}
        </svg>
      </div>
      <div className="px-4 pb-3 space-y-1">
        {CLASS_NAMES.map((n) => (
          <div key={n} className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-2 text-slate-400">
              <span className="w-2.5 h-2.5 rounded-sm" style={{ background: CLASS_COLORS[n] }} />
              <span className="capitalize">{n}</span>
            </span>
            <span className="mono text-slate-200">AUC {(aucs[n] ?? 0).toFixed(3)}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
