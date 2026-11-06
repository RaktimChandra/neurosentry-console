"""Tests for the hybrid TCN + PINN model."""
import torch

from app.config import settings
from app.core.models import HybridForecaster, TCNEncoder, PINNHead, jr_rhs_torch


def test_tcn_shape_and_causal():
    enc = TCNEncoder(settings.tcn_channels, settings.tcn_kernel,
                     settings.tcn_dilations, settings.tcn_dropout)
    enc.eval()  # disable dropout stochasticity for the causality check
    with torch.no_grad():
        x = torch.randn(2, 1, 256)
        y = enc(x)
        assert y.shape == (2, settings.tcn_channels[-1], 256)
        # Causality: future input shouldn't change past output
        x2 = x.clone()
        x2[:, :, 200:] = torch.randn_like(x2[:, :, 200:])
        y2 = enc(x2)
        assert torch.allclose(y[:, :, :50], y2[:, :, :50], atol=1e-5)


def test_pinn_head_bounded():
    head = PINNHead(16, hidden=32, state_dim=6)
    z = torch.randn(3, 16, 128) * 100  # extreme input
    s = head(z)
    assert s.shape == (3, 6, 128)
    # Should be physiologically bounded by tanh * scale + bias
    assert torch.isfinite(s).all()
    assert s[:, 0].abs().max() < 30
    assert s[:, 3].abs().max() < 600


def test_hybrid_forward_shapes():
    m = HybridForecaster(settings)
    x = torch.randn(4, settings.window_samples)
    out = m(x)
    assert out["logits"].shape == (4, 3)
    assert out["horizon"].shape == (4,)
    assert out["state"].shape == (4, 6, settings.window_samples)
    assert out["recon"].shape == (4, settings.window_samples)


def test_hybrid_backprop():
    """Loss over all three heads should produce gradients on all learnable params."""
    m = HybridForecaster(settings)
    x = torch.randn(2, settings.window_samples)
    out = m(x)
    loss = (
        out["logits"].sum()
        + out["horizon"].sum() * 0.1
        + out["state"].sum() * 0.01
        + out["recon"].sum() * 0.01
    )
    loss.backward()
    missing = [n for n, p in m.named_parameters()
               if p.requires_grad and p.grad is None]
    assert not missing, f"params without grad: {missing}"


def test_jr_rhs_torch_matches_numpy():
    from app.core.jansen_rit import rhs as rhs_np, JansenRitParams
    state_np = __import__("numpy").array([2.0, 5.0, 3.0, 0.1, 0.2, 0.3])
    p = JansenRitParams()
    out_np = rhs_np(state_np, 200.0, p)
    state_t = torch.tensor(state_np, dtype=torch.float32).view(1, 6, 1)
    p_t = torch.tensor([[200.0]], dtype=torch.float32)
    out_t = jr_rhs_torch(state_t, p_t, A=p.A, B=p.B).view(-1).numpy()
    import numpy as np
    assert np.allclose(out_np, out_t, atol=1e-3)
