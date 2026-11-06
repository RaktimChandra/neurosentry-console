import { useApp } from "../lib/store";

const COMPONENT_LABELS = [
  { name: "y₀", desc: "Pyramidal PSP", color: "#7dd3fc" },
  { name: "y₁", desc: "Excitatory PSP", color: "#22d3a0" },
  { name: "y₂", desc: "Inhibitory PSP", color: "#f472b6" },
  { name: "ẏ₀", desc: "Pyramidal rate", color: "#60a5fa" },
  { name: "ẏ₁", desc: "Excitatory rate", color: "#34d399" },
  { name: "ẏ₂", desc: "Inhibitory rate", color: "#fb7185" },
];

export function LatentStatePanel() {
  const frame = useApp((s) => s.frame);
  return (
    <section className="panel">
      <div className="panel-header">
        <span>Jansen-Rit Latent State</span>
        <span className="mono text-[10px] text-slate-500 normal-case">
          6-D inferred ŝ(t)
        </span>
      </div>
      <div className="p-3 grid grid-cols-3 gap-2">
        {COMPONENT_LABELS.map((c, i) => (
          <LatentSparkline
            key={c.name}
            label={c.name}
            desc={c.desc}
            color={c.color}
            data={frame?.state?.[i] ?? []}
          />
        ))}
      </div>
    </section>
  );
}

function LatentSparkline({
  label, desc, color, data,
}: {
  label: string; desc: string; color: string; data: number[];
}) {
  const w = 180, h = 54;
  let path = "";
  if (data.length > 1) {
    let lo = Infinity, hi = -Infinity;
    for (const v of data) { if (v < lo) lo = v; if (v > hi) hi = v; }
    const pad = (hi - lo) * 0.1 || 1;
    lo -= pad; hi += pad;
    const n = data.length;
    for (let i = 0; i < n; i++) {
      const x = (i / (n - 1)) * (w - 2) + 1;
      const y = h - ((data[i] - lo) / (hi - lo)) * (h - 10) - 5;
      path += (i === 0 ? "M" : "L") + x.toFixed(2) + " " + y.toFixed(2) + " ";
    }
  }
  const latestVal = data.length ? data[data.length - 1] : null;
  return (
    <div className="rounded-md bg-ink-800/50 border border-ink-700/50 p-2.5 flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-baseline gap-1.5">
          <span className="mono text-sm font-semibold" style={{ color }}>
            {label}
          </span>
          <span className="text-[10px] text-slate-500">{desc}</span>
        </div>
        <span className="mono text-[10px] text-slate-400">
          {latestVal !== null ? latestVal.toFixed(2) : "--"}
        </span>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ height: h }} preserveAspectRatio="none">
        <line x1="0" y1={h / 2} x2={w} y2={h / 2} stroke="#1a2238" strokeDasharray="2 3" />
        <path d={path} fill="none" stroke={color} strokeWidth="1.5"
          strokeLinecap="round" strokeLinejoin="round"
          style={{ filter: `drop-shadow(0 0 2px ${color})` }} />
      </svg>
    </div>
  );
}
