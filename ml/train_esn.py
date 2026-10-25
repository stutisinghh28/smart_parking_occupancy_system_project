"""
Training and data preparation pipeline for the Echo State Network (ESN).
Generates realistic parking time series data, trains the ESN,
evaluates 15-minute and 30-minute forecasts, and saves model weights.
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, Dict

# Support direct execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml.esn import EchoStateNetwork

MODEL_FILE_PATH = os.path.join(os.path.dirname(__file__), "esn_model.npz")


def generate_synthetic_occupancy(
    days: int = 14,
    step_minutes: int = 5,
    seed: int = 42
) -> pd.DataFrame:
    """
    Simulates realistic 6-slot parking lot dynamics across multiple days.
    Reflects diurnal commuter peaks (morning 8-10 AM, evening 5-7 PM),
    lunch rush (12-2 PM), night vacancies, and weekend differences.
    """
    rng = np.random.default_rng(seed)
    total_steps = (days * 24 * 60) // step_minutes
    start_time = datetime(2026, 10, 1, 0, 0, 0)

    timestamps = [start_time + timedelta(minutes=i * step_minutes) for i in range(total_steps)]
    
    # Initialize slot states (0: free, 1: occupied)
    slots = np.zeros((total_steps, 6), dtype=int)
    
    current_slots = np.zeros(6, dtype=int)

    for i, t in enumerate(timestamps):
        hour = t.hour + t.minute / 60.0
        is_weekend = t.weekday() >= 5

        # Base arrival probability curve by time of day
        if is_weekend:
            # Weekend pattern: late morning peak, relaxed evening
            base_prob = 0.2 + 0.4 * np.exp(-((hour - 14) ** 2) / 16)
        else:
            # Weekday pattern: double peak (workday + lunch)
            morning_peak = 0.85 * np.exp(-((hour - 9) ** 2) / 4)
            lunch_peak = 0.65 * np.exp(-((hour - 13) ** 2) / 3)
            evening_peak = 0.50 * np.exp(-((hour - 18) ** 2) / 5)
            base_prob = np.clip(0.1 + morning_peak + lunch_peak + evening_peak, 0.05, 0.95)

        # Transition each slot with realistic stickiness (cars stay ~30-180 min)
        for s in range(6):
            if current_slots[s] == 0:
                # Slot is free: probability of a new car arriving
                arrival_chance = base_prob * 0.15
                if rng.random() < arrival_chance:
                    current_slots[s] = 1
            else:
                # Slot is occupied: probability of departure
                # Departure probability is higher in late afternoon or night
                departure_bias = 0.15 if (hour >= 17 or hour <= 6) else 0.05
                if rng.random() < departure_bias:
                    current_slots[s] = 0

        slots[i] = current_slots.copy()

    df = pd.DataFrame({
        "timestamp": timestamps,
        "slot_1": slots[:, 0],
        "slot_2": slots[:, 1],
        "slot_3": slots[:, 2],
        "slot_4": slots[:, 3],
        "slot_5": slots[:, 4],
        "slot_6": slots[:, 5],
    })
    
    df["occupied_count"] = df[["slot_1", "slot_2", "slot_3", "slot_4", "slot_5", "slot_6"]].sum(axis=1)
    df["free_count"] = 6 - df["occupied_count"]
    return df


def prepare_esn_features(
    df: pd.DataFrame,
    step_minutes: int = 5
) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Transforms dataframe into normalized ESN inputs and multi-step targets:
    Inputs: [free_count / 6.0, sin(hour), cos(hour)]
    Targets: [free_count @ t+15min, free_count @ t+30min]
    """
    steps_15min = 15 // step_minutes  # 3 steps
    steps_30min = 30 // step_minutes  # 6 steps

    # Time features (cyclical hour encoding)
    hours = df["timestamp"].dt.hour + df["timestamp"].dt.minute / 60.0
    sin_hour = np.sin(2 * np.pi * hours / 24.0).to_numpy()
    cos_hour = np.cos(2 * np.pi * hours / 24.0).to_numpy()

    free_norm = (df["free_count"].to_numpy() / 6.0)

    # Input matrix X: (T, 3)
    X_full = np.column_stack([free_norm, sin_hour, cos_hour])

    # Target matrix Y: [free_count @ t+3, free_count @ t+6]
    target_15m = df["free_count"].shift(-steps_15min).to_numpy()
    target_30m = df["free_count"].shift(-steps_30min).to_numpy()

    # Drop trailing NaN values due to lookahead shifts
    valid_len = len(df) - steps_30min
    X = X_full[:valid_len]
    Y = np.column_stack([target_15m[:valid_len], target_30m[:valid_len]])

    df_valid = df.iloc[:valid_len].copy()
    return X, Y, df_valid


def train_and_save_esn(
    days: int = 14,
    save_path: str = MODEL_FILE_PATH
) -> Dict[str, float]:
    """Train the Echo State Network and save the trained weights."""
    print(f"[*] Generating {days} days of realistic parking occupancy dynamics...")
    df = generate_synthetic_occupancy(days=days, step_minutes=5)
    
    X, Y, _ = prepare_esn_features(df, step_minutes=5)
    
    # Train / Test split (80% train, 20% test)
    split_idx = int(0.8 * len(X))
    X_train, Y_train = X[:split_idx], Y[:split_idx]
    X_test, Y_test = X[split_idx:], Y[split_idx:]

    print(f"[*] Training Echo State Network (Train samples: {len(X_train)}, Test samples: {len(X_test)})...")
    esn = EchoStateNetwork(
        n_inputs=3,
        n_reservoir=100,
        n_outputs=2,           # Output 0: 15-min forecast, Output 1: 30-min forecast
        spectral_radius=0.85,
        sparsity=0.85,
        leaking_rate=0.40,
        ridge_param=1.0,
        input_scaling=0.3,
        seed=42
    )

    train_metrics = esn.fit(X_train, Y_train, washout=60)
    print(f"[+] Train MSE: {train_metrics['train_mse']:.4f}, Train MAE: {train_metrics['train_mae']:.4f}")

    # Evaluate on test set
    test_preds = esn.predict(X_test)
    test_mse_15m = float(np.mean((Y_test[:, 0] - test_preds[:, 0]) ** 2))
    test_mae_15m = float(np.mean(np.abs(Y_test[:, 0] - test_preds[:, 0])))

    test_mse_30m = float(np.mean((Y_test[:, 1] - test_preds[:, 1]) ** 2))
    test_mae_30m = float(np.mean(np.abs(Y_test[:, 1] - test_preds[:, 1])))

    print(f"[+] 15-Min Test - MSE: {test_mse_15m:.4f}, MAE: {test_mae_15m:.4f} free slots")
    print(f"[+] 30-Min Test - MSE: {test_mse_30m:.4f}, MAE: {test_mae_30m:.4f} free slots")

    # Retrain on full dataset to maximize prediction accuracy in deployment
    print("[*] Retraining on full historical set for deployment...")
    esn.reset_state()
    full_metrics = esn.fit(X, Y, washout=60)
    
    esn.save(save_path)
    print(f"[+] Model successfully saved to: {save_path}")

    return {
        "train_mse": full_metrics["train_mse"],
        "train_mae": full_metrics["train_mae"],
        "test_mae_15m": test_mae_15m,
        "test_mae_30m": test_mae_30m
    }


if __name__ == "__main__":
    train_and_save_esn()
