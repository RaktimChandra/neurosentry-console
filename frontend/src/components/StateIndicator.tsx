import clsx from "clsx";
import { useApp } from "../lib/store";
import { CLASS_LABELS, CLASS_COLORS, CLASS_NAMES, type ClassName } from "../lib/types";

export function StateIndicator() {
  const { frame } = useApp();
  const cls: ClassName = (frame?.class_name ?? "interictal") as ClassName;
  const confidence = frame?.confidence ?? 0;
  const groundTruth = frame?.ground_truth ?? 0;
  const correct = frame ? frame.class_index === frame.ground_truth : true;
  const truthName = CLASS_NAMES[groundTruth];

  const color = CLASS_COLORS[cls];
  const probs = frame?.probs ?? [1, 0, 0];

  return (
    <section
      className={clsx(
        "panel transition-all duration-500",
        cls === "ictal" && "ring-1 ring-signal-red/30 shadow-glow shadow-signal-red/30",
        cls === "preictal" && "ring-1 ring-signal-amber/30 shadow-glow shadow-signal-amber/25",
      )}
    >
      <div className="panel-header">
        <span>Current State</span>
        <span className="mono text-slate-500 text-[10px]">LIVE INFERENCE</span>
      </div>

      <div className="p-5 flex items-stretch gap-6">
        {/* Primary readout */}
        <div className="flex-1 flex items-center gap-5">
          <div className="relative">
            <div
              className={clsx(
                "w-20 h-20 rounded-full flex items-center justify-center",
                "border-2 transition-all duration-500",
                cls === "ictal" && "border-signal-red animate-pulseFast",
                cls === "preictal" && "border-signal-amber animate-pulse",
                cls === "interictal" && "border-signal-green",
              )}
              style={{
                background: `radial-gradient(closest-side, ${color}25, transparent)`,
                boxShadow: `0 0 36px -4px ${color}99`,
              }}
            >
              <span className="mono text-xl font-semibold" style={{ color }}>
                {Math.round(confidence * 100)}%
              </span>
            </div>
          </div>
          <div className="flex flex-col gap-1">
            <div className="text-[11px] mono text-slate-500 tracking-[0.2em]">
              CORTICAL STATE
            </div>
            <div className="text-3xl font-semibold tracking-wide" style={{ color }}>
              {CLASS_LABELS[cls]}
            </div>
            <div className="mono text-xs text-slate-500">
              Ground truth: <span className="text-slate-300">{CLASS_LABELS[truthName]}</span>
              <span className={clsx("ml-2", correct ? "text-signal-green" : "text-signal-red")}>
                {correct ? "✓ MATCH" : "✗ MISMATCH"}
              </span>
            </div>
          </div>
        </div>

        {/* Probability bars */}
        <div className="flex-1 flex flex-col gap-2 justify-center min-w-[220px]">
          {CLASS_NAMES.map((name, i) => {
            const p = probs[i] ?? 0;
            return (
              <div key={name} className="flex items-center gap-3">
                <span
                  className="w-24 mono text-[10px] uppercase tracking-wider"
                  style={{ color: CLASS_COLORS[name] }}
                >
                  {name}
                </span>
                <div className="flex-1 h-2 bg-ink-800 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${p * 100}%`,
                      background: CLASS_COLORS[name],
                      boxShadow: `0 0 8px ${CLASS_COLORS[name]}99`,
                    }}
                  />
                </div>
                <span className="mono text-xs text-slate-300 w-12 text-right">
                  {p.toFixed(3)}
                </span>
              </div>
            );
          })}
        </div>

        {/* Warning horizon */}
        {frame && cls === "preictal" && frame.horizon_s > 0 && (
          <div className="flex flex-col items-end justify-center min-w-[100px] border-l border-ink-700 pl-5">
            <div className="text-[10px] mono text-slate-500 tracking-[0.15em]">
              SEIZURE IN
            </div>
            <div className="mono text-2xl font-semibold text-signal-amber mt-1">
              {frame.horizon_s.toFixed(1)}s
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
