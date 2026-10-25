"""
Unit tests for Echo State Network (ESN).
Verifies reservoir initialization, spectral radius scaling,
fit procedure, multi-step predictions, and save/load persistence.
"""

import os
import sys
import tempfile
import numpy as np
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml.esn import EchoStateNetwork


def test_esn_initialization_and_spectral_radius():
    n_inputs = 3
    n_res = 80
    n_out = 2
    target_sr = 0.90

    esn = EchoStateNetwork(
        n_inputs=n_inputs,
        n_reservoir=n_res,
        n_outputs=n_out,
        spectral_radius=target_sr,
        sparsity=0.8,
        seed=123
    )

    assert esn.W_in.shape == (n_res, n_inputs)
    assert esn.W_res.shape == (n_res, n_res)
    assert esn.W_bias.shape == (n_res,)
    assert esn.W_out is None

    # Verify spectral radius
    eigenvalues = np.linalg.eigvals(esn.W_res)
    calculated_sr = np.max(np.abs(eigenvalues))
    assert np.isclose(calculated_sr, target_sr, atol=1e-4)


def test_esn_fit_and_prediction():
    np.random.seed(42)
    T = 200
    # Synthetic series: sine waves
    t = np.linspace(0, 20, T)
    X = np.column_stack([np.sin(t), np.cos(t), np.sin(2 * t)])
    Y = np.column_stack([np.sin(t + 0.5), np.sin(t + 1.0)])

    esn = EchoStateNetwork(
        n_inputs=3,
        n_reservoir=60,
        n_outputs=2,
        spectral_radius=0.9,
        seed=42
    )

    metrics = esn.fit(X, Y, washout=20)
    assert "train_mse" in metrics
    assert "train_mae" in metrics
    assert esn.W_out is not None
    # Readout shape: (n_outputs, 1 + n_inputs + n_reservoir)
    assert esn.W_out.shape == (2, 1 + 3 + 60)

    # Predict sequence
    preds = esn.predict(X[:30])
    assert preds.shape == (30, 2)


def test_esn_single_step_predict_and_clip():
    esn = EchoStateNetwork(n_inputs=3, n_reservoir=50, n_outputs=2, seed=42)
    # Dummy training to get W_out
    X = np.random.randn(80, 3)
    Y = np.random.uniform(0, 6, size=(80, 2))
    esn.fit(X, Y, washout=10)

    u = np.array([0.5, 0.2, -0.1])
    pred = esn.predict_next(u)
    assert pred.shape == (2,)
    # Output must be clipped between 0 and 6 (parking capacity)
    assert 0.0 <= pred[0] <= 6.0
    assert 0.0 <= pred[1] <= 6.0


def test_esn_save_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test_esn.npz")
        
        esn1 = EchoStateNetwork(n_inputs=3, n_reservoir=40, n_outputs=2, seed=99)
        X = np.random.randn(60, 3)
        Y = np.random.uniform(0, 6, size=(60, 2))
        esn1.fit(X, Y, washout=10)

        esn1.save(filepath)
        assert os.path.exists(filepath)

        # Load back
        esn2 = EchoStateNetwork.load(filepath)
        assert esn2.n_inputs == esn1.n_inputs
        assert esn2.n_reservoir == esn1.n_reservoir
        assert esn2.n_outputs == esn1.n_outputs
        np.testing.assert_allclose(esn1.W_in, esn2.W_in)
        np.testing.assert_allclose(esn1.W_res, esn2.W_res)
        np.testing.assert_allclose(esn1.W_out, esn2.W_out)
