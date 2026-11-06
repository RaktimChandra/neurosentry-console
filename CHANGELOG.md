# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Multi-channel support (graph-coupled Jansen-Rit column network)
- Real EEG dataset transfer (CHB-MIT, Bonn)
- Uncertainty quantification via deep ensembles
- Live user annotations on recorded windows for prospective fine-tuning

## [1.0.0] — 2026-11-06

### Added
- Hybrid TCN + PINN hybrid model with 72,554 parameters, binary-compatible with the parent `neurosentry` research repo's checkpoints
- Jansen-Rit neural-mass simulator (pure NumPy, RK4 integrator, three regime presets)
- Bootstrap trainer that self-produces a trained checkpoint on first boot (~45s on CPU) with stabilized normalized physics residual
- Six synthesized patient recordings with varied seizure schedules
- FastAPI backend with REST + WebSocket streaming inference (~5–50ms per window on CPU)
- React 18 + TypeScript frontend with hospital-monitor dark theme
- Canvas-rendered scrolling EEG scope at 128 Hz with PINN-reconstruction overlay
- 6-component Jansen-Rit latent state visualization
- Hybrid-vs-baseline ablation panel using precomputed research test-set metrics
- Keyboard shortcuts (spacebar to pause, 1-6 for speed, arrow keys to seek)
- Multi-stage Dockerfile for single-image deployment (CPU-only torch to keep image lean)
- Deployment configs for Railway, Render, Fly.io, and docker-compose
- GitHub Actions CI: pytest + tsc + vite build + docker build on every push
- 19/19 backend tests passing (Jansen-Rit simulator, model architecture, REST API)
- Architecture and deployment documentation
