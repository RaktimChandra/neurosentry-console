import clsx from "clsx";
import { useApp } from "../lib/store";

export function PatientSelector() {
  const { patients, selectedPid, selectPatient } = useApp();
  return (
    <section className="panel flex-shrink-0">
      <div className="panel-header">
        <span>Recordings</span>
        <span className="text-slate-500 mono text-[10px]">{patients.length} available</span>
      </div>
      <ul className="p-2 space-y-1 max-h-[32vh] overflow-y-auto">
        {patients.map((p) => {
          const active = p.id === selectedPid;
          return (
            <li key={p.id}>
              <button
                onClick={() => selectPatient(p.id)}
                className={clsx(
                  "w-full text-left px-3 py-2.5 rounded-md border transition",
                  "flex flex-col gap-0.5",
                  active
                    ? "border-signal-green/40 bg-signal-green/10 text-slate-50 shadow-glow shadow-signal-green/20"
                    : "border-transparent hover:border-ink-600 hover:bg-ink-800/60 text-slate-300",
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{p.label}</span>
                  <span className="mono text-[10px] text-slate-500">
                    {p.duration_s.toFixed(0)}s
                  </span>
                </div>
                <span className="text-xs text-slate-500 leading-snug">
                  {p.description}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
