"""
Pydantic schemas for data validation, API input payloads, and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SlotReading(BaseModel):
    """Single slot measurement from ultrasonic sensor."""
    slot_id: int = Field(..., ge=1, le=6, description="Slot index (1 to 6)")
    distance_cm: float = Field(..., ge=0.0, le=500.0, description="Calculated distance in cm")
    is_occupied: bool = Field(..., description="True if car detected, False otherwise")
    echo_time_us: Optional[float] = Field(None, ge=0.0, description="Measured echo pulse width in microseconds")


class TelemetryPayload(BaseModel):
    """Batch of slot readings sent periodically by ESP8266 or Simulator."""
    readings: List[SlotReading]
    device_id: Optional[str] = "STM32_ESP8266_HUB"
    timestamp: Optional[datetime] = None


class SlotStatus(BaseModel):
    slot_id: int
    distance_cm: float
    is_occupied: bool
    status_label: str  # "OCCUPIED" or "FREE"
    last_updated: datetime


class SystemStatusResponse(BaseModel):
    total_slots: int = 6
    occupied_count: int
    free_count: int
    slots: List[SlotStatus]
    last_updated: datetime


class ForecastResponse(BaseModel):
    timestamp: datetime
    current_free: int
    predicted_free_15min: float
    predicted_free_30min: float
    model_algorithm: str = "Echo State Network (ESN)"
    horizon_15min_rounded: int
    horizon_30min_rounded: int


class HistoricalOccupancyPoint(BaseModel):
    timestamp: datetime
    occupied_count: int
    free_count: int
