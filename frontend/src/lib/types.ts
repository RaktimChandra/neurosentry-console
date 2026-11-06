// Shared TypeScript types for the console frontend.

export type ClassName = "interictal" | "preictal" | "ictal";
export type ClassIndex = 0 | 1 | 2;

export const CLASS_NAMES: ClassName[] = ["interictal", "preictal", "ictal"];

export const CLASS_COLORS: Record<ClassName, string> = {
  interictal: "#22d3a0",
  preictal: "#ffb020",
  ictal: "#ff3360",
};

export const CLASS_LABELS: Record<ClassName, string> = {
  interictal: "INTERICTAL",
  preictal: "PREICTAL",
  ictal: "ICTAL",
};

export interface PatientSummary {
  id: string;
  label: string;
  description: string;
  duration_s: number;
  fs: number;
}

export interface PatientSchedule {
  regime: ClassName;
  start_s: number;
  end_s: number;
}

export interface PatientMeta {
  id: string;
  label: string;
  description: string;
  duration_s: number;
  fs: number;
  n_samples: number;
  seed: number;
  schedule: PatientSchedule[];
}

export interface StreamMeta {
  type: "meta";
  patient_id: string;
  meta: PatientMeta;
  n_windows: number;
  window_samples: number;
  stride_samples: number;
}

export interface StreamFrame {
  type: "frame";
  i: number;
  t0: number;
  t1: number;
  eeg: number[];
  labels: number[];
  probs: [number, number, number];
  class_index: ClassIndex;
  class_name: ClassName;
  confidence: number;
  horizon_s: number;
  ground_truth: ClassIndex;
  state: number[][];     // 6 x (T/4)
  recon: number[];       // T/2
  latency_ms: number;
}

export interface StreamDone {
  type: "done";
  last_index: number;
}

export interface StreamError {
  type: "error";
  detail: string;
}

export type StreamMessage = StreamMeta | StreamFrame | StreamDone | StreamError;

export interface TestMetrics {
  accuracy: number;
  macro_f1: number;
  confusion_matrix?: number[][];
  auc_per_class: Record<string, number>;
  false_alarm_per_hour: number;
  median_warning_horizon_s: number;
  n_alarms?: number;
  physics_residual_mean?: number;
  support_per_class?: Record<string, number>;
}

export interface AllMetrics {
  hybrid: { model: string; test: TestMetrics; params: number; training?: unknown };
  baseline: { model: string; test: TestMetrics; params: number };
  delta: { accuracy: number; macro_f1: number };
}
