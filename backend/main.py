"""
FastAPI application for Smart Parking Occupancy Predictor.
Handles sensor telemetry ingestion from ESP8266 or simulator,
status queries, historical series, and Echo State Network (ESN) forecasts.
"""

import os
import sys
from datetime import datetime, timezone
from typing import List, Optional
import numpy as np
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.database import (
    init_db, get_db, SlotTelemetry, OccupancySnapshot, ForecastLog
)
from backend.schemas import (
    TelemetryPayload, SystemStatusResponse, SlotStatus,
    ForecastResponse, HistoricalOccupancyPoint
)
from ml.esn import EchoStateNetwork
from ml.train_esn import MODEL_FILE_PATH, train_and_save_esn

# Initialize database tables on startup
init_db()

app = FastAPI(
    title="Smart Parking Occupancy Predictor API",
    description="IoT telemetry ingestion for STM32 + ESP8266 and ESN-based occupancy forecasting",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global cache for loaded ESN model
_esn_model: Optional[EchoStateNetwork] = None


def get_loaded_esn() -> EchoStateNetwork:
    """Loads ESN model weights into memory if not already cached."""
    global _esn_model
    if _esn_model is None:
        if not os.path.exists(MODEL_FILE_PATH):
            # Train if no saved weights exist
            train_and_save_esn(days=14, save_path=MODEL_FILE_PATH)
        _esn_model = EchoStateNetwork.load(MODEL_FILE_PATH)
    return _esn_model


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_loaded": os.path.exists(MODEL_FILE_PATH)
    }


@app.post("/api/telemetry")
def ingest_telemetry(payload: TelemetryPayload, db: Session = Depends(get_db)):
    """
    Ingests sensor readings from STM32 + ESP8266 Wi-Fi hub or software simulator.
    Validates slot measurements, stores raw readings, and updates occupancy snapshot.
    """
    if len(payload.readings) == 0:
        raise HTTPException(status_code=400, detail="Empty readings batch received.")

    now = payload.timestamp or datetime.now(timezone.utc)
    slot_map = {}

    # Store individual slot telemetry
    for reading in payload.readings:
        slot_map[reading.slot_id] = reading.is_occupied
        db_telemetry = SlotTelemetry(
            timestamp=now,
            slot_id=reading.slot_id,
            distance_cm=reading.distance_cm,
            is_occupied=reading.is_occupied,
            echo_time_us=reading.echo_time_us
        )
        db.add(db_telemetry)

    # Compute overall snapshot for 6 slots
    occupied_count = sum(1 for occupied in slot_map.values() if occupied)
    free_count = 6 - occupied_count

    snapshot = OccupancySnapshot(
        timestamp=now,
        total_slots=6,
        occupied_count=occupied_count,
        free_count=free_count,
        slot_1_occupied=slot_map.get(1, False),
        slot_2_occupied=slot_map.get(2, False),
        slot_3_occupied=slot_map.get(3, False),
        slot_4_occupied=slot_map.get(4, False),
        slot_5_occupied=slot_map.get(5, False),
        slot_6_occupied=slot_map.get(6, False)
    )
    db.add(snapshot)
    db.commit()

    return {
        "status": "success",
        "timestamp": now.isoformat(),
        "readings_ingested": len(payload.readings),
        "occupied_count": occupied_count,
        "free_count": free_count
    }


@app.get("/api/status", response_model=SystemStatusResponse)
def get_current_status(db: Session = Depends(get_db)):
    """
    Returns the real-time status of all 6 slots and aggregate occupancy.
    """
    slots_data = []
    latest_ts = datetime.now(timezone.utc)

    # Query the most recent reading for each slot (1 to 6)
    for slot_id in range(1, 7):
        latest_reading = (
            db.query(SlotTelemetry)
            .filter(SlotTelemetry.slot_id == slot_id)
            .order_by(desc(SlotTelemetry.timestamp), desc(SlotTelemetry.id))
            .first()
        )

        if latest_reading:
            latest_ts = max(latest_ts, latest_reading.timestamp) if slots_data else latest_reading.timestamp
            is_occ = latest_reading.is_occupied
            dist = latest_reading.distance_cm
            ts = latest_reading.timestamp
        else:
            # Default fallback if no data ingested yet
            is_occ = False
            dist = 200.0  # Empty slot distance
            ts = datetime.now(timezone.utc)

        slots_data.append(SlotStatus(
            slot_id=slot_id,
            distance_cm=dist,
            is_occupied=is_occ,
            status_label="OCCUPIED" if is_occ else "FREE",
            last_updated=ts
        ))

    occupied_count = sum(1 for s in slots_data if s.is_occupied)
    free_count = 6 - occupied_count

    return SystemStatusResponse(
        total_slots=6,
        occupied_count=occupied_count,
        free_count=free_count,
        slots=slots_data,
        last_updated=latest_ts
    )


@app.get("/api/forecast", response_model=ForecastResponse)
def get_occupancy_forecast(db: Session = Depends(get_db)):
    """
    Uses the trained Echo State Network (ESN) to forecast
    the number of free parking slots 15 minutes and 30 minutes ahead.
    Feeds recent historical snapshots to warm up the reservoir state dynamics.
    """
    esn = get_loaded_esn()

    # Query recent snapshots for dynamic reservoir state alignment
    recent_snapshots = (
        db.query(OccupancySnapshot)
        .order_by(desc(OccupancySnapshot.timestamp), desc(OccupancySnapshot.id))
        .limit(15)
        .all()
    )

    now = datetime.now(timezone.utc)

    if recent_snapshots:
        ordered_snaps = list(reversed(recent_snapshots))
        feature_rows = []
        for s in ordered_snaps:
            ts = s.timestamp
            h = ts.hour + ts.minute / 60.0
            feature_rows.append([
                s.free_count / 6.0,
                np.sin(2 * np.pi * h / 24.0),
                np.cos(2 * np.pi * h / 24.0)
            ])
        X_seq = np.array(feature_rows, dtype=np.float64)
        current_free = ordered_snaps[-1].free_count
    else:
        # Fallback to current instant state
        status = get_current_status(db)
        current_free = status.free_count
        h = now.hour + now.minute / 60.0
        X_seq = np.array([[
            current_free / 6.0,
            np.sin(2 * np.pi * h / 24.0),
            np.cos(2 * np.pi * h / 24.0)
        ]], dtype=np.float64)

    # Propagate through reservoir
    preds = esn.predict(X_seq)
    final_pred = preds[-1]

    pred_15m = float(np.clip(final_pred[0], 0.0, 6.0))
    pred_30m = float(np.clip(final_pred[1], 0.0, 6.0))

    # Log prediction into database
    log_entry = ForecastLog(
        timestamp=now,
        current_free=current_free,
        predicted_free_15min=pred_15m,
        predicted_free_30min=pred_30m
    )
    db.add(log_entry)
    db.commit()

    return ForecastResponse(
        timestamp=now,
        current_free=current_free,
        predicted_free_15min=round(pred_15m, 2),
        predicted_free_30min=round(pred_30m, 2),
        model_algorithm="Echo State Network (ESN)",
        horizon_15min_rounded=int(round(pred_15m)),
        horizon_30min_rounded=int(round(pred_30m))
    )


@app.get("/api/history", response_model=List[HistoricalOccupancyPoint])
def get_history(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    """
    Returns recent chronological occupancy snapshots for charting.
    """
    records = (
        db.query(OccupancySnapshot)
        .order_by(desc(OccupancySnapshot.timestamp), desc(OccupancySnapshot.id))
        .limit(limit)
        .all()
    )
    # Reverse to return ascending chronological order
    records = list(reversed(records))
    return [
        HistoricalOccupancyPoint(
            timestamp=r.timestamp,
            occupied_count=r.occupied_count,
            free_count=r.free_count
        )
        for r in records
    ]


@app.post("/api/train-esn")
def trigger_train_esn():
    """
    Retrains the ESN on synthetic or historical data and reloads the memory cache.
    """
    global _esn_model
    metrics = train_and_save_esn(days=14, save_path=MODEL_FILE_PATH)
    _esn_model = EchoStateNetwork.load(MODEL_FILE_PATH)
    return {
        "status": "success",
        "message": "Echo State Network successfully retrained and reloaded.",
        "metrics": metrics
    }
