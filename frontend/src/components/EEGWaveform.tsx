import { useEffect, useRef } from "react";
import { useApp } from "../lib/store";
import { CLASS_COLORS, CLASS_NAMES } from "../lib/types";

// Rolling scope that shows the EEG input (cyan) and PINN reconstruction (pink)
// along with a background colour representing the predicted cortical state.

const BG_FILL = "#0a0e1a";
const GRID = "#152042";
const AXIS = "#30406a";

export function EEGWaveform() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const bufferRef = useRef<{
    eeg: number[];
    recon: number[];
    classes: number[];
    truths: number[];
  }>({ eeg: [], recon: [], classes: [], truths: [] });

  const frame = useApp((s) => s.frame);

  // Ingest new frame into rolling buffer
  useEffect(() => {
    if (!frame) return;
    const buf = bufferRef.current;
    const stride = 128; // one window stride worth of new samples
    // Append latest stride samples from the incoming window
    const start = Math.max(0, frame.eeg.length - stride);
    const newSamples = frame.eeg.slice(start);
    // Reconstruction is downsampled by 2 → upsample by holding neighbours
    const reconFull: number[] = [];
    for (let i = 0; i < frame.recon.length; i++) {
      reconFull.push(frame.recon[i], frame.recon[i]);
    }
    const newRecon = reconFull.slice(Math.max(0, reconFull.length - stride));

    buf.eeg.push(...newSamples);
    buf.recon.push(...newRecon);
    for (let i = 0; i < newSamples.length; i++) {
      buf.classes.push(frame.class_index);
      buf.truths.push(frame.ground_truth);
    }
    // Keep last 10 seconds
    const cap = 128 * 10;
    if (buf.eeg.length > cap) {
      buf.eeg.splice(0, buf.eeg.length - cap);
      buf.recon.splice(0, buf.recon.length - cap);
      buf.classes.splice(0, buf.classes.length - cap);
      buf.truths.splice(0, buf.truths.length - cap);
    }
  }, [frame]);

  // Render loop
  useEffect(() => {
    let raf = 0;
    const draw = () => {
      const canvas = canvasRef.current;
      const container = containerRef.current;
      if (canvas && container) {
        const dpr = window.devicePixelRatio || 1;
        const cssW = container.clientWidth;
        const cssH = container.clientHeight;
        if (canvas.width !== cssW * dpr) {
          canvas.width = cssW * dpr;
          canvas.height = cssH * dpr;
        }
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          renderScope(ctx, cssW, cssH, bufferRef.current);
        }
      }
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <section className="panel flex-1 flex flex-col min-h-0">
      <div className="panel-header">
        <div className="flex items-center gap-4">
          <span>EEG Scope</span>
          <div className="flex items-center gap-3 text-[10px] mono normal-case tracking-normal">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-[2px] bg-trace-eeg inline-block" />
              <span className="text-slate-400">Observed EEG</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-[2px] bg-[#f472b6] inline-block" />
              <span className="text-slate-400">PINN reconstruction</span>
            </span>
          </div>
        </div>
        <span className="mono text-[10px] text-slate-500">128 Hz · last 10 s</span>
      </div>
      <div ref={containerRef} className="flex-1 min-h-0 relative">
        <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
      </div>
      <GroundTruthBar />
    </section>
  );
}

// ------------ bottom regime strip (truth vs predicted) ------------

interface Buffer {
  eeg: number[];
  recon: number[];
  classes: number[];
  truths: number[];
}

// Share buffer ref between scope and strip
const bufferRefGlobal: { current: Buffer } = {
  current: { eeg: [], recon: [], classes: [], truths: [] },
};

function GroundTruthBar() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    let raf = 0;
    const draw = () => {
      const canvas = canvasRef.current;
      if (canvas) {
        const dpr = window.devicePixelRatio || 1;
        const cssW = canvas.parentElement?.clientWidth ?? 800;
        const cssH = 26;
        if (canvas.width !== cssW * dpr) {
          canvas.width = cssW * dpr;
          canvas.height = cssH * dpr;
        }
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          renderStrip(ctx, cssW, cssH, bufferRefGlobal.current);
        }
      }
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div className="border-t border-ink-700/60">
      <div className="flex items-center justify-between px-4 py-1 text-[10px] mono text-slate-500 tracking-wider uppercase">
        <span>Regime</span>
        <span className="flex items-center gap-3">
          <span>Truth (upper)</span><span>·</span><span>Predicted (lower)</span>
        </span>
      </div>
      <canvas ref={canvasRef} className="w-full block" style={{ height: 26 }} />
    </div>
  );
}

function renderScope(
  ctx: CanvasRenderingContext2D, W: number, H: number,
  buf: Buffer,
) {
  // propagate to strip
  bufferRefGlobal.current = buf;

  ctx.fillStyle = BG_FILL;
  ctx.fillRect(0, 0, W, H);

  // --- background regime bands based on predicted class
  if (buf.classes.length > 1) {
    const n = buf.classes.length;
    const step = W / n;
    for (let i = 0; i < n; i++) {
      const cls = buf.classes[i];
      const color = CLASS_COLORS[CLASS_NAMES[cls]];
      ctx.fillStyle = `${color}0D`; // 5% opacity
      ctx.fillRect(i * step, 0, step + 1, H);
    }
  }

  // --- time grid (1-second major gridlines)
  ctx.strokeStyle = GRID;
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let s = 0; s <= 10; s++) {
    const x = (s / 10) * W;
    ctx.moveTo(x, 0);
    ctx.lineTo(x, H);
  }
  // amplitude midline
  ctx.moveTo(0, H / 2);
  ctx.lineTo(W, H / 2);
  ctx.stroke();

  // --- axis ticks
  ctx.fillStyle = AXIS;
  ctx.font = "10px JetBrains Mono, monospace";
  for (let s = 0; s <= 10; s++) {
    const x = (s / 10) * W;
    ctx.fillText(`-${10 - s}s`, x + 4, H - 6);
  }

  // --- waveform
  if (buf.eeg.length < 2) return;
  const n = buf.eeg.length;
  const yMid = H / 2;
  // dynamic autoscale over last visible window
  let lo = Infinity, hi = -Infinity;
  for (let i = 0; i < n; i++) {
    const v = buf.eeg[i];
    if (v < lo) lo = v;
    if (v > hi) hi = v;
    const r = buf.recon[i];
    if (r < lo) lo = r;
    if (r > hi) hi = r;
  }
  const pad = (hi - lo) * 0.1 || 1;
  lo -= pad; hi += pad;
  const sy = (v: number) => H - ((v - lo) / (hi - lo)) * (H - 20) - 10;

  // reconstruction first (underlay)
  ctx.strokeStyle = "#f472b6";
  ctx.lineWidth = 1.2;
  ctx.globalAlpha = 0.75;
  ctx.beginPath();
  for (let i = 0; i < n; i++) {
    const x = (i / (n - 1)) * W;
    const y = sy(buf.recon[i] ?? 0);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
  ctx.globalAlpha = 1;

  // EEG trace with soft glow
  ctx.shadowColor = "#7dd3fc";
  ctx.shadowBlur = 4;
  ctx.strokeStyle = "#7dd3fc";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  for (let i = 0; i < n; i++) {
    const x = (i / (n - 1)) * W;
    const y = sy(buf.eeg[i]);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
  ctx.shadowBlur = 0;

  // y-axis label
  ctx.fillStyle = AXIS;
  ctx.font = "10px JetBrains Mono, monospace";
  ctx.fillText("Amplitude (mV)", 8, 14);
}

function renderStrip(
  ctx: CanvasRenderingContext2D, W: number, H: number,
  buf: { classes: number[]; truths: number[] },
) {
  ctx.fillStyle = BG_FILL;
  ctx.fillRect(0, 0, W, H);
  if (buf.classes.length === 0) return;
  const n = buf.classes.length;
  const step = W / n;
  const halfH = (H - 2) / 2;
  // truth row (top)
  for (let i = 0; i < n; i++) {
    const cls = buf.truths[i];
    const color = CLASS_COLORS[CLASS_NAMES[cls]];
    ctx.fillStyle = color;
    ctx.fillRect(i * step, 1, step + 1, halfH);
  }
  // predicted row (bottom)
  for (let i = 0; i < n; i++) {
    const cls = buf.classes[i];
    const color = CLASS_COLORS[CLASS_NAMES[cls]];
    ctx.fillStyle = color;
    ctx.fillRect(i * step, H - halfH - 1, step + 1, halfH);
  }
}
