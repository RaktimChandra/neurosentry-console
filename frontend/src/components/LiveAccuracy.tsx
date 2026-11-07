import { useApp } from "../lib/store";

/**
 * Live running accuracy over this playback session: pred-vs-ground-truth across
 * all windows streamed so far. Updates on every frame.
 */
export function LiveAccuracy() {
  const history = useApp((s) => s.history);
  if (history.length === 0) return null;
  const correct = history.filter((f) => f.class_index === f.ground_truth).length;
  const acc = correct / history.length;
  const pct = (acc * 100).toFixed(1);
  const color = acc >= 0.95 ? "#22d3a0" : acc >= 0.85 ? "#ffb020" : "#ff3360";
  return (
    <div className="pill" title="Running accuracy over this playback session">
      <span className="text-slate-400">Session acc</span>
      <span className="mono" style={{ color }}>{pct}%</span>
      <span className="text-slate-500 text-[9px]">
        {correct}/{history.length}
      </span>
    </div>
  );
}
