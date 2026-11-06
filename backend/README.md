# NeuroSentry Console — Backend

FastAPI + PyTorch service that embeds the trained hybrid TCN + PINN model and
serves the Vite-built SPA from `/`.

## Development

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

First boot synthesises 6 patient recordings (~20 s) and bootstraps a hybrid
model from 24 fresh JR-simulated training recordings (~45 s on CPU).
Both are cached to disk for subsequent boots.

## Tests

```bash
python -m pytest tests/ -v
```

## API

See `docs/ARCHITECTURE.md` in the repo root.

## Dropping in a real trained checkpoint

If you have a `hybrid.pt` from the parent research repo
([RaktimChandra/neurosentry](https://github.com/RaktimChandra/neurosentry)), copy
it into `checkpoints/hybrid.pt` before first boot. The inference engine
loads it instead of training a new one. The format matches:

```python
torch.save({
    "model_state": model.state_dict(),
    "config": {...},
}, "checkpoints/hybrid.pt")
```

## Layout

```
app/
  main.py                # FastAPI app factory, SPA mounting
  config.py              # Pydantic settings
  core/
    jansen_rit.py        # JR neural-mass simulator (NumPy)
    models.py            # Hybrid TCN+PINN PyTorch implementation
    training.py          # Bootstrap trainer
    inference.py         # Runtime inference wrapper
    patients.py          # Synthetic patient cache
    metrics.py           # Precomputed test-set metrics
  api/
    routes/
      health.py          # /api/health, /api/system
      patients.py        # /api/patients[/{pid}]
      inference.py       # /api/infer/*
      metrics.py         # /api/metrics
      stream.py          # /ws/stream/{pid}
tests/
checkpoints/             # created on first boot
data/patients/           # created on first boot
```
