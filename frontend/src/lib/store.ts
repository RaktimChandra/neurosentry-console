// Global app state with Zustand.

import { create } from "zustand";
import type { PatientSummary, StreamFrame, StreamMeta, AllMetrics } from "./types";

interface AppState {
  // Catalogue
  patients: PatientSummary[];
  selectedPid: string | null;
  metrics: AllMetrics | null;

  // Stream state
  meta: StreamMeta | null;
  frame: StreamFrame | null;
  history: StreamFrame[];           // last N frames for timeline rendering

  // Playback
  playing: boolean;
  speed: 1 | 2 | 4 | 8 | 16 | 32;

  // Connection
  connected: boolean;
  wsError: string | null;

  // Actions
  setPatients: (p: PatientSummary[]) => void;
  setMetrics: (m: AllMetrics) => void;
  selectPatient: (pid: string) => void;
  resetStream: () => void;
  onMeta: (m: StreamMeta) => void;
  onFrame: (f: StreamFrame) => void;
  setConnected: (c: boolean, err?: string | null) => void;
  setPlaying: (p: boolean) => void;
  setSpeed: (s: AppState["speed"]) => void;
}

export const useApp = create<AppState>((set) => ({
  patients: [],
  selectedPid: null,
  metrics: null,
  meta: null,
  frame: null,
  history: [],
  playing: true,
  speed: 4,
  connected: false,
  wsError: null,

  setPatients: (patients) => set({ patients }),
  setMetrics: (metrics) => set({ metrics }),
  selectPatient: (pid) =>
    set({ selectedPid: pid, meta: null, frame: null, history: [], wsError: null }),
  resetStream: () => set({ meta: null, frame: null, history: [] }),
  onMeta: (meta) => set({ meta }),
  onFrame: (frame) =>
    set((s) => ({
      frame,
      history: [...s.history.slice(-199), frame],
    })),
  setConnected: (connected, err = null) => set({ connected, wsError: err }),
  setPlaying: (playing) => set({ playing }),
  setSpeed: (speed) => set({ speed }),
}));
