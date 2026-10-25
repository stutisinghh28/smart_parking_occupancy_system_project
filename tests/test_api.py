"""
Integration tests for FastAPI endpoints using TestClient.
Tests telemetry ingestion, real-time status calculation, and ESN predictions.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.main import app
from backend.database import init_db

client = TestClient(app)


def setup_module(module):
    """Ensure clean test environment."""
    init_db()


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_ingest_telemetry():
    # 2 occupied, 4 free
    payload = {
        "readings": [
            {"slot_id": 1, "distance_cm": 35.5, "is_occupied": True, "echo_time_us": 2066.1},
            {"slot_id": 2, "distance_cm": 210.0, "is_occupied": False, "echo_time_us": 12222.0},
            {"slot_id": 3, "distance_cm": 42.1, "is_occupied": True, "echo_time_us": 2450.2},
            {"slot_id": 4, "distance_cm": 205.0, "is_occupied": False, "echo_time_us": 11931.0},
            {"slot_id": 5, "distance_cm": 218.4, "is_occupied": False, "echo_time_us": 12710.9},
            {"slot_id": 6, "distance_cm": 202.0, "is_occupied": False, "echo_time_us": 11756.4}
        ],
        "device_id": "TEST_HUB"
    }

    response = client.post("/api/telemetry", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["readings_ingested"] == 6
    assert data["occupied_count"] == 2
    assert data["free_count"] == 4


def test_get_current_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["total_slots"] == 6
    assert data["occupied_count"] == 2
    assert data["free_count"] == 4
    assert len(data["slots"]) == 6

    # Verify slot 1 is occupied and slot 2 is free
    s1 = next(s for s in data["slots"] if s["slot_id"] == 1)
    s2 = next(s for s in data["slots"] if s["slot_id"] == 2)
    assert s1["is_occupied"] is True
    assert s1["status_label"] == "OCCUPIED"
    assert s2["is_occupied"] is False
    assert s2["status_label"] == "FREE"


def test_get_forecast():
    response = client.get("/api/forecast")
    assert response.status_code == 200
    data = response.json()
    assert data["model_algorithm"] == "Echo State Network (ESN)"
    assert 0.0 <= data["predicted_free_15min"] <= 6.0
    assert 0.0 <= data["predicted_free_30min"] <= 6.0
    assert 0 <= data["horizon_15min_rounded"] <= 6
    assert 0 <= data["horizon_30min_rounded"] <= 6


def test_get_history():
    response = client.get("/api/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "occupied_count" in data[0]
    assert "free_count" in data[0]
