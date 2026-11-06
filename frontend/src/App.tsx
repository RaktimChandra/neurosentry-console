import { useEffect } from "react";
import { TopBar } from "./components/TopBar";
import { PatientSelector } from "./components/PatientSelector";
import { StateIndicator } from "./components/StateIndicator";
import { EEGWaveform } from "./components/EEGWaveform";
import { LatentStatePanel } from "./components/LatentStatePanel";
import { MetricsPanel } from "./components/MetricsPanel";
import { Controls } from "./components/Controls";
import { Timeline } from "./components/Timeline";
import { ShortcutsHint } from "./components/ShortcutsHint";
import { useApp } from "./lib/store";
import { fetchPatients, fetchMetrics } from "./lib/api";
import { useStream } from "./hooks/useStream";

export default function App() {
  const { patients, selectedPid, selectPatient, setPatients, setMetrics } = useApp();

  // Initial load
  useEffect(() => {
    fetchPatients()
      .then((p) => { setPatients(p); if (p.length > 0) selectPatient(p[0].id); })
      .catch((e) => console.error("fetchPatients", e));
    fetchMetrics().then(setMetrics).catch((e) => console.error("fetchMetrics", e));
  }, [setPatients, selectPatient, setMetrics]);

  const { seek } = useStream(selectedPid);

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const st = useApp.getState();
      if (e.key === " ") { e.preventDefault(); st.setPlaying(!st.playing); }
      if (e.key === "ArrowRight") st.frame && seek(Math.min((st.frame.i ?? 0) + 5, (st.meta?.n_windows ?? 1) - 1));
      if (e.key === "ArrowLeft") st.frame && seek(Math.max((st.frame.i ?? 0) - 5, 0));
      if (e.key >= "1" && e.key <= "6") {
        const speeds = [1, 2, 4, 8, 16, 32] as const;
        st.setSpeed(speeds[parseInt(e.key, 10) - 1]);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [seek]);

  return (
    <div className="h-full flex flex-col">
      <TopBar />
      <main className="flex-1 min-h-0 grid grid-cols-12 gap-3 p-3 overflow-hidden">
        {/* Left sidebar */}
        <aside className="col-span-12 lg:col-span-3 flex flex-col gap-3 min-h-0 overflow-y-auto">
          <PatientSelector />
          <Timeline />
          <div className="panel">
            <div className="panel-header">
              <span>About</span>
              <span className="mono text-[10px] text-slate-500 normal-case">v1.0</span>
            </div>
            <div className="p-4 text-xs text-slate-400 leading-relaxed space-y-2">
              <p>
                <span className="text-slate-200 font-medium">NeuroSentry</span> is a
                hybrid Temporal Convolutional Network + Physics-Informed Neural Network
                for pre-ictal EEG forecasting, grounded in the Jansen-Rit neural-mass
                model.
              </p>
              <p>
                This console plays back any held-out recording, runs the trained hybrid
                model on each 4-second window, and overlays the decoded
                6-D Jansen-Rit state. The dashed pink trace on the scope is the
                EEG proxy decoded from the inferred state — the model's audit trail.
              </p>
              <p className="pt-1 text-slate-500">
                Model: 72,554 params · Causal TCN (dilations 1, 2, 4, 8) + PINN head.
              </p>
              <p className="pt-1 text-slate-500">
                <kbd className="mono text-[10px] px-1 bg-ink-800 border border-ink-700 rounded">Space</kbd> play/pause,
                {" "}<kbd className="mono text-[10px] px-1 bg-ink-800 border border-ink-700 rounded">1-6</kbd> speed,
                {" "}<kbd className="mono text-[10px] px-1 bg-ink-800 border border-ink-700 rounded">←/→</kbd> seek.
              </p>
            </div>
          </div>
        </aside>

        {/* Main workspace */}
        <section className="col-span-12 lg:col-span-9 flex flex-col gap-3 min-h-0 overflow-y-auto">
          <StateIndicator />
          <div className="min-h-[340px] flex">
            <EEGWaveform />
          </div>
          <Controls onSeek={seek} />
          <LatentStatePanel />
          <MetricsPanel />
        </section>
      </main>

      {patients.length === 0 && (
        <div className="fixed inset-0 flex items-center justify-center bg-ink-950/80 z-50 pointer-events-none">
          <div className="pill"><span className="led led-amber" /> Starting up…</div>
        </div>
      )}
      <ShortcutsHint />
    </div>
  );
}
