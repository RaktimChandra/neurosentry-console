// WebSocket connection hook.

import { useEffect, useRef } from "react";
import { streamUrl } from "../lib/api";
import { useApp } from "../lib/store";
import type { StreamMessage } from "../lib/types";

export function useStream(pid: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const {
    onMeta, onFrame, setConnected, playing, speed, resetStream,
  } = useApp();

  useEffect(() => {
    if (!pid) return;
    resetStream();

    const ws = new WebSocket(streamUrl(pid));
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false, "WebSocket error");

    ws.onmessage = (ev) => {
      let msg: StreamMessage;
      try { msg = JSON.parse(ev.data); } catch { return; }
      if (msg.type === "meta") onMeta(msg);
      else if (msg.type === "frame") onFrame(msg);
      else if (msg.type === "error") setConnected(false, msg.detail);
    };

    return () => {
      try { ws.close(); } catch {}
      wsRef.current = null;
      setConnected(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pid]);

  // Sync playing/speed to server
  useEffect(() => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ cmd: playing ? "resume" : "pause" }));
  }, [playing]);

  useEffect(() => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ cmd: "speed", x: speed }));
  }, [speed]);

  // Imperative command
  const seek = (index: number) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ cmd: "seek", index }));
  };

  return { seek };
}
