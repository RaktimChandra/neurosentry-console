// REST + WebSocket client.

import type {
  AllMetrics, PatientSummary, PatientMeta,
} from "./types";

const base = ""; // same-origin; dev proxy handles /api and /ws

export async function fetchPatients(): Promise<PatientSummary[]> {
  const r = await fetch(`${base}/api/patients`);
  if (!r.ok) throw new Error(`fetchPatients ${r.status}`);
  const j = await r.json();
  return j.patients as PatientSummary[];
}

export async function fetchPatientMeta(pid: string): Promise<PatientMeta> {
  const r = await fetch(`${base}/api/patients/${pid}`);
  if (!r.ok) throw new Error(`fetchPatientMeta ${r.status}`);
  const j = await r.json();
  return j.meta as PatientMeta;
}

export async function fetchMetrics(): Promise<AllMetrics> {
  const r = await fetch(`${base}/api/metrics`);
  if (!r.ok) throw new Error(`fetchMetrics ${r.status}`);
  return (await r.json()) as AllMetrics;
}

export function streamUrl(pid: string): string {
  const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  return `${scheme}//${host}/ws/stream/${pid}`;
}
