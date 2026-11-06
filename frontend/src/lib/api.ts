// REST + WebSocket client with retry and timeout defaults.

import type {
  AllMetrics, PatientSummary, PatientMeta,
} from "./types";

const base = ""; // same-origin; dev proxy handles /api and /ws

/** Fetch with timeout + 2 retries on transient 5xx / network errors. */
async function fetchJson<T>(
  path: string,
  { timeoutMs = 10_000, retries = 2 }: { timeoutMs?: number; retries?: number } = {},
): Promise<T> {
  let lastErr: unknown;
  for (let attempt = 0; attempt <= retries; attempt++) {
    const ctrl = new AbortController();
    const timer = window.setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const r = await fetch(`${base}${path}`, { signal: ctrl.signal });
      window.clearTimeout(timer);
      if (r.ok) return (await r.json()) as T;
      // Retry on 5xx; bail on 4xx
      if (r.status < 500) throw new Error(`${path} → ${r.status}`);
      lastErr = new Error(`${path} → ${r.status}`);
    } catch (e) {
      window.clearTimeout(timer);
      lastErr = e;
      if ((e as Error).name === "AbortError") lastErr = new Error(`${path} timed out`);
    }
    if (attempt < retries) {
      await new Promise((r) => setTimeout(r, 300 * (attempt + 1)));
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error(String(lastErr));
}

export async function fetchPatients(): Promise<PatientSummary[]> {
  const j = await fetchJson<{ patients: PatientSummary[] }>("/api/patients");
  return j.patients;
}

export async function fetchPatientMeta(pid: string): Promise<PatientMeta> {
  const j = await fetchJson<{ meta: PatientMeta }>(`/api/patients/${pid}`);
  return j.meta;
}

export async function fetchMetrics(): Promise<AllMetrics> {
  return fetchJson<AllMetrics>("/api/metrics");
}

export function streamUrl(pid: string): string {
  const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  return `${scheme}//${host}/ws/stream/${pid}`;
}
