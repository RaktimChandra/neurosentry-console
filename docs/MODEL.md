# Model Details

The console embeds the same **hybrid Temporal Convolutional Network + Physics-Informed Neural Network** architecture as the parent research repo at [`RaktimChandra/neurosentry`](https://github.com/RaktimChandra/neurosentry).

## Architecture summary

| Block            | Spec                                   | Params  |
|------------------|----------------------------------------|---------|
| TCN block 1      | Dilated causal conv, d=1, 1→32 ch      | 10,304  |
| TCN block 2      | Dilated causal conv, d=2, 32→32 ch     |  6,208  |
| TCN block 3      | Dilated causal conv, d=4, 32→64 ch     | 12,544  |
| TCN block 4      | Dilated causal conv, d=8, 64→64 ch     | 12,288  |
| Classifier head  | AvgPool → 64 → 3                       |  4,355  |
| Horizon head     | MaxPool → 64 → 1                       |  4,225  |
| PINN head        | 2-layer MLP + tanh scaling → 6         | 12,998  |
| Aux. projections | Residual skips, 1×1 convs              |  9,632  |
| **Total**        |                                        | **72,554** |

All hyperparameters live in `backend/app/config.py` and are overridable via `NEUROSENTRY_*` env vars.

## Composite loss

```
L = λ_cls · L_cls  +  λ_hor · L_hor  +  λ_phys · L_phys  +  λ_rec · L_rec
```

Default weights: `(1.0, 0.2, 0.01, 0.1)`.

- `L_cls` — class-weighted cross-entropy on three-class regime classification
- `L_hor` — Huber (smooth-L1) loss on seconds-to-seizure, masked to preictal windows
- `L_phys` — **normalised** weak-form Jansen-Rit residual; per-component RMS normalisation + `log1p` clamp for numerical stability
- `L_rec` — MSE between input EEG and the decoded PINN reconstruction (y₁ − y₂)

The `log1p` + per-component normalisation is critical: without it the raw residual spans 4+ orders of magnitude (the a² term is 10⁴ while the sigmoid term is O(1)) and training diverges within a few hundred steps. The current implementation has trained cleanly across 10+ random seeds.

## Jansen-Rit regimes

| Regime      | B (mV) | p_mu | Description                                         |
|-------------|--------|------|-----------------------------------------------------|
| interictal  | 22.0   | 220  | Canonical alpha rhythm                              |
| preictal    | 17.0   | 260  | Mild inhibition drop, broadband power increase      |
| ictal       | 14.0   | 300  | Spike-wave discharges (Wendling 2000 regime)        |

Lowering `B` (inhibitory synaptic gain) and raising `p_mu` (mean external drive) is the Wendling (2000) recipe for epileptic dynamics in the Jansen-Rit model.

## Checkpoint format

```python
torch.save({
    "model_state": model.state_dict(),
    "config": {
        "tcn_channels": [32, 32, 64, 64],
        "tcn_kernel": 3,
        "tcn_dilations": [1, 2, 4, 8],
        "tcn_dropout": 0.1,
        "pinn_hidden": 64,
        "state_dim": 6,
        "fs": 128,
        "window_sec": 4.0,
    },
}, "checkpoints/hybrid.pt")
```

Drop a checkpoint from the research repo into `backend/checkpoints/hybrid.pt` before first boot and the inference engine will use it instead of self-training.

## Research test-set performance

Numbers below are from the parent research repo's held-out test set (n = 504 windows):

| Metric                | Hybrid  | Baseline (TCN only) | Δ        |
|-----------------------|---------|---------------------|----------|
| Accuracy              | 0.9742  | 0.9683              | +0.0059  |
| Macro F1              | 0.9682  | 0.9571              | +0.0111  |
| Interictal AUC        | 1.000   | 1.000               |  0.000   |
| Preictal AUC          | 0.9932  | 0.9926              | +0.0006  |
| Ictal AUC             | 0.9922  | 0.9913              | +0.0009  |
| False alarms/hour     | 59.02   | 14.75               | +44.27   |

The physics prior does not dramatically change raw accuracy on the synthetic benchmark (both models saturate near 97%) — its value is the interpretable 6-D neurophysiological latent state that the baseline cannot produce.

## Bootstrap training

On fresh deployments (no `hybrid.pt` present) the backend self-trains a small checkpoint on startup:

- 24 synthesised recordings × 60 s each → ~1,500 training windows
- 6 epochs with Adam + cosine LR schedule
- ~45 seconds on a Railway starter instance (CPU)
- Final validation accuracy typically 92–95 %

Subsequent restarts load the cached `checkpoints/hybrid.pt` and skip training.
