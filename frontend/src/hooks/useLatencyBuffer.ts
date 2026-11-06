// Rolling buffer of the last N inference latencies, for a tiny sparkline on
// the top bar. Pure state hook, no side effects.

import { useRef, useEffect } from "react";
import { useApp } from "../lib/store";

export function useLatencyBuffer(size: number = 60) {
  const buf = useRef<number[]>([]);
  const frame = useApp((s) => s.frame);

  useEffect(() => {
    if (!frame) return;
    buf.current.push(frame.latency_ms);
    if (buf.current.length > size) {
      buf.current.splice(0, buf.current.length - size);
    }
  }, [frame, size]);

  return buf;
}
