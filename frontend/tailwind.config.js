/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Hospital-monitor dark theme
        ink: {
          950: "#05070d",
          900: "#0a0e1a",
          850: "#0e1322",
          800: "#121829",
          700: "#1a2238",
          600: "#232c47",
          500: "#2e3756",
          400: "#4a5478",
        },
        // Signal states
        signal: {
          green: "#22d3a0",    // interictal — safe
          greenGlow: "#22d3a040",
          amber: "#ffb020",    // preictal — warning
          amberGlow: "#ffb02040",
          red: "#ff3360",      // ictal — critical
          redGlow: "#ff336040",
        },
        trace: {
          eeg: "#7dd3fc",
          recon: "#f472b6",
          axis: "#30406a",
          grid: "#1a2238",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        glow: "0 0 24px -4px var(--tw-shadow-color)",
        panel: "0 1px 0 rgba(255,255,255,0.03) inset, 0 20px 40px rgba(0,0,0,0.3)",
      },
      animation: {
        pulse: "pulse 1.8s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        pulseFast: "pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};
