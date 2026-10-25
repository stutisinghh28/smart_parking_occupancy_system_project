"""
Echo State Network (ESN) implementation using NumPy.
Designed for multi-step time-series forecasting (15-min and 30-min parking occupancy).
Strictly adheres to reservoir computing principles without external ML libraries.
"""

import numpy as np
import os
import json
from typing import Tuple, Optional, Dict, Any


class EchoStateNetwork:
    """
    Echo State Network (ESN) with leaky-integrator reservoir neurons
    and Ridge Regression readout.
    """
    def __init__(
        self,
        n_inputs: int = 3,
        n_reservoir: int = 120,
        n_outputs: int = 2,
        spectral_radius: float = 0.95,
        sparsity: float = 0.85,
        leaking_rate: float = 0.35,
        ridge_param: float = 1e-4,
        input_scaling: float = 0.5,
        seed: int = 42
    ):
        """
        Parameters:
            n_inputs: Number of input features (e.g. [current_free_slots, sin(time), cos(time)])
            n_reservoir: Number of recurrent reservoir neurons (Nx)
            n_outputs: Number of prediction targets (e.g. [free_slots_15min, free_slots_30min])
            spectral_radius: Target spectral radius (max absolute eigenvalue) of W_res < 1.0
            sparsity: Proportion of zero weights in reservoir connection matrix W_res
            leaking_rate: Leak rate alpha in (0, 1] governing reservoir time dynamics
            ridge_param: Tikhonov regularization parameter (lambda) for linear readout
            input_scaling: Scale factor for input weights W_in
            seed: Seed for reproducible weight initialization
        """
        self.n_inputs = n_inputs
        self.n_reservoir = n_reservoir
        self.n_outputs = n_outputs
        self.spectral_radius = spectral_radius
        self.sparsity = sparsity
        self.leaking_rate = leaking_rate
        self.ridge_param = ridge_param
        self.input_scaling = input_scaling
        self.seed = seed

        # Model weights
        self.W_in: Optional[np.ndarray] = None
        self.W_res: Optional[np.ndarray] = None
        self.W_bias: Optional[np.ndarray] = None
        self.W_out: Optional[np.ndarray] = None

        # State tracking
        self.state: np.ndarray = np.zeros(self.n_reservoir)

        self._initialize_weights()

    def _initialize_weights(self):
        rng = np.random.default_rng(self.seed)

        # Input weight matrix: uniformly distributed in [-input_scaling, input_scaling]
        self.W_in = rng.uniform(
            -self.input_scaling,
            self.input_scaling,
            size=(self.n_reservoir, self.n_inputs)
        )

        # Reservoir bias vector
        self.W_bias = rng.uniform(-0.1, 0.1, size=self.n_reservoir)

        # Sparse internal reservoir weight matrix
        raw_res = rng.uniform(-1.0, 1.0, size=(self.n_reservoir, self.n_reservoir))
        mask = rng.random(size=(self.n_reservoir, self.n_reservoir)) < self.sparsity
        raw_res[mask] = 0.0

        # Scale reservoir to ensure Echo State Property (spectral radius < 1)
        eigenvalues = np.linalg.eigvals(raw_res)
        max_eigenval = np.max(np.abs(eigenvalues))
        if max_eigenval > 0:
            self.W_res = raw_res * (self.spectral_radius / max_eigenval)
        else:
            self.W_res = raw_res

    def reset_state(self):
        """Reset internal reservoir state to zero."""
        self.state = np.zeros(self.n_reservoir)

    def _step(self, u: np.ndarray, current_state: np.ndarray) -> np.ndarray:
        """
        Computes one time-step update for leaky integrator reservoir neurons:
        x(t) = (1 - alpha) * x(t-1) + alpha * tanh(W_in * u(t) + W_res * x(t-1) + W_bias)
        """
        pre_activation = (
            np.dot(self.W_in, u) +
            np.dot(self.W_res, current_state) +
            self.W_bias
        )
        new_state = (1.0 - self.leaking_rate) * current_state + self.leaking_rate * np.tanh(pre_activation)
        return new_state

    def fit(self, X: np.ndarray, Y: np.ndarray, washout: int = 50) -> Dict[str, float]:
        """
        Harvests reservoir states on sequence X, and computes Ridge Regression readout weights W_out.

        Parameters:
            X: Input array of shape (T, n_inputs)
            Y: Target array of shape (T, n_outputs)
            washout: Number of initial warm-up timesteps to discard (reservoir transient)

        Returns:
            Dictionary with training metrics (MSE, MAE)
        """
        T = X.shape[0]
        if T <= washout:
            raise ValueError(f"Training sequence length ({T}) must be greater than washout ({washout}).")

        # Collect state matrix
        states = np.zeros((T, self.n_reservoir))
        current_state = np.zeros(self.n_reservoir)

        for t in range(T):
            current_state = self._step(X[t], current_state)
            states[t] = current_state

        # Keep state from the end of training
        self.state = current_state.copy()

        # Discard washout period
        X_used = X[washout:]
        states_used = states[washout:]
        Y_used = Y[washout:]

        # Extended reservoir state matrix: [1 (bias), inputs, reservoir_states]
        # Shape: (T_used, 1 + n_inputs + n_reservoir)
        ones = np.ones((states_used.shape[0], 1))
        S = np.hstack([ones, X_used, states_used])

        # Ridge Regression: W_out = Y^T * S * (S^T * S + lambda * I)^(-1)
        # Using S_transpose:
        # S: (N_samples, Dim) -> Dim = 1 + n_inputs + n_reservoir
        dim = S.shape[1]
        reg = self.ridge_param * np.eye(dim)
        # Solve: (S^T * S + reg) * W_out^T = S^T * Y
        STS = np.dot(S.T, S) + reg
        STY = np.dot(S.T, Y_used)
        
        # W_out shape: (n_outputs, dim)
        self.W_out = np.linalg.solve(STS, STY).T

        # Calculate training predictions and metrics
        Y_pred = np.dot(S, self.W_out.T)
        mse = float(np.mean((Y_used - Y_pred) ** 2))
        mae = float(np.mean(np.abs(Y_used - Y_pred)))

        return {"train_mse": mse, "train_mae": mae}

    def predict(self, X: np.ndarray, preserve_state: bool = False) -> np.ndarray:
        """
        Generate predictions for input sequence X of shape (T, n_inputs).
        Returns predictions of shape (T, n_outputs).
        """
        if self.W_out is None:
            raise RuntimeError("Model has not been trained yet. Call fit() first.")

        T = X.shape[0]
        predictions = np.zeros((T, self.n_outputs))
        
        current_state = self.state.copy() if preserve_state else np.zeros(self.n_reservoir)

        for t in range(T):
            current_state = self._step(X[t], current_state)
            extended_s = np.concatenate([[1.0], X[t], current_state])
            predictions[t] = np.dot(self.W_out, extended_s)

        if preserve_state:
            self.state = current_state

        return predictions

    def predict_next(self, u: np.ndarray) -> np.ndarray:
        """
        Single-step forecast given current input vector u of shape (n_inputs,).
        Updates internal reservoir state in-place.
        Returns predicted target vector of shape (n_outputs,).
        """
        if self.W_out is None:
            raise RuntimeError("Model has not been trained yet.")

        self.state = self._step(u, self.state)
        extended_s = np.concatenate([[1.0], u, self.state])
        pred = np.dot(self.W_out, extended_s)
        # Clip parking occupancy predictions to valid range [0, 6]
        return np.clip(pred, 0.0, 6.0)

    def save(self, filepath: str):
        """Save model configuration and weights to a .npz file."""
        meta = {
            "n_inputs": self.n_inputs,
            "n_reservoir": self.n_reservoir,
            "n_outputs": self.n_outputs,
            "spectral_radius": self.spectral_radius,
            "sparsity": self.sparsity,
            "leaking_rate": self.leaking_rate,
            "ridge_param": self.ridge_param,
            "input_scaling": self.input_scaling,
            "seed": self.seed
        }
        np.savez(
            filepath,
            metadata=json.dumps(meta),
            W_in=self.W_in,
            W_res=self.W_res,
            W_bias=self.W_bias,
            W_out=self.W_out if self.W_out is not None else np.array([]),
            state=self.state
        )

    @classmethod
    def load(cls, filepath: str) -> "EchoStateNetwork":
        """Load an ESN model from a saved .npz file."""
        data = np.load(filepath, allow_pickle=True)
        meta = json.loads(str(data["metadata"]))

        esn = cls(
            n_inputs=meta["n_inputs"],
            n_reservoir=meta["n_reservoir"],
            n_outputs=meta["n_outputs"],
            spectral_radius=meta["spectral_radius"],
            sparsity=meta["sparsity"],
            leaking_rate=meta["leaking_rate"],
            ridge_param=meta["ridge_param"],
            input_scaling=meta["input_scaling"],
            seed=meta["seed"]
        )
        esn.W_in = data["W_in"]
        esn.W_res = data["W_res"]
        esn.W_bias = data["W_bias"]
        esn.W_out = data["W_out"] if data["W_out"].size > 0 else None
        esn.state = data["state"] if "state" in data else np.zeros(esn.n_reservoir)
        return esn
