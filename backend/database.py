"""
Database configuration and SQLAlchemy ORM models for parking occupancy and forecasts.
"""

import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

def get_utc_now():
    return datetime.now(timezone.utc)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "parking.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.abspath(DB_PATH)}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class SlotTelemetry(Base):
    """
    Individual HC-SR04 sensor reading record per slot.
    Directly reflects data transmitted from STM32 + ESP8266 or Simulator.
    """
    __tablename__ = "slot_telemetry"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=get_utc_now, index=True)
    slot_id = Column(Integer, index=True)          # 1 to 6
    distance_cm = Column(Float, nullable=False)    # Measured ultrasonic distance
    is_occupied = Column(Boolean, nullable=False)  # Classified status (distance < threshold)
    echo_time_us = Column(Float, nullable=True)    # Raw timer pulse width in microseconds


class OccupancySnapshot(Base):
    """
    Consolidated state of all 6 parking slots at a single point in time.
    """
    __tablename__ = "occupancy_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=get_utc_now, index=True)
    total_slots = Column(Integer, default=6)
    occupied_count = Column(Integer, nullable=False)
    free_count = Column(Integer, nullable=False)
    slot_1_occupied = Column(Boolean, default=False)
    slot_2_occupied = Column(Boolean, default=False)
    slot_3_occupied = Column(Boolean, default=False)
    slot_4_occupied = Column(Boolean, default=False)
    slot_5_occupied = Column(Boolean, default=False)
    slot_6_occupied = Column(Boolean, default=False)


class ForecastLog(Base):
    """
    Logs ESN predictions for auditing and accuracy tracking over time.
    """
    __tablename__ = "forecast_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=get_utc_now, index=True)
    current_free = Column(Integer, nullable=False)
    predicted_free_15min = Column(Float, nullable=False)
    predicted_free_30min = Column(Float, nullable=False)


def init_db():
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency helper for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
