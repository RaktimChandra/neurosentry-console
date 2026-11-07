import { useEffect, useRef } from "react";
import { useApp } from "../lib/store";

/**
 * Tiny inline sparkline showing the last 60 inference latencies in milliseconds.
 * Lives in the TopBar next to the inference-time pill to give a quick visual
 * cue that the model is keeping up with streaming demand.
 */
export function LatencySparkline() {
  const frame = useApp((s) => s.frame);
  const buf = useRef<number[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!frame) return;
    buf.current.push(frame.latency_ms);
    if (buf.current.length > 60) buf.current.splice(0, buf.current.length - 60);
    draw();
  }, [frame]);

  const draw = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    const w = 60, h = 16;
    if (canvas.width !== w * dpr) {
      canvas.width = w * dpr;
      canvas.height = h * dpr;
    }
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const n = buf.current.length;
    if (n < 2) return;
    const max = Math.max(...buf.current, 50); // floor at 50ms for stable scale
    ctx.strokeStyle = "#22d3a0";
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const x = (i / (n - 1)) * w;
      const y = h - (buf.current[i] / max) * (h - 2) - 1;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  };

  return (
    <canvas
      ref={canvasRef}
      className="inline-block align-middle ml-1"
      style={{ width: 60, height: 16 }}
      aria-hidden
    />
  );
}
