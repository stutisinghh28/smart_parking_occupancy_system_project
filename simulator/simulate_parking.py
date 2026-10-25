"""
Ultrasonic Sensor Simulation for 6-Slot Parking Lot.
Simulates HC-SR04 pulse dynamics, distance calculation (d = echo_time_us / 58.2),
occupancy thresholding (<80cm = OCCUPIED), and posts telemetry to FastAPI backend.
"""

import time
import argparse
import random
import requests
from datetime import datetime, timezone
from typing import List, Dict

API_TELEMETRY_URL = "http://127.0.0.1:8000/api/telemetry"
OCCUPANCY_THRESHOLD_CM = 80.0
SPEED_OF_SOUND_DIVISOR = 58.2  # Time in microseconds per cm round-trip


class UltrasonicSensorSimulator:
    def __init__(self, slot_id: int):
        self.slot_id = slot_id
        self.is_occupied = False
        # Empty bay distance: ~190 - 230 cm
        # Car parked distance: ~25 - 65 cm

    def measure(self) -> Dict:
        """
        Simulates HC-SR04 physics:
        Computes physical echo time in microseconds and resulting distance in cm.
        """
        if self.is_occupied:
            # Distance to vehicle roof/hood with slight sensor jitter
            distance_cm = round(random.uniform(28.0, 58.0), 1)
        else:
            # Distance to floor/asphalt when slot is vacant
            distance_cm = round(random.uniform(195.0, 225.0), 1)

        # Microseconds echo pulse width: echo_us = distance_cm * 58.2
        echo_us = round(distance_cm * SPEED_OF_SOUND_DIVISOR, 1)

        # Firmware threshold classification
        classified_occupied = distance_cm < OCCUPANCY_THRESHOLD_CM

        return {
            "slot_id": self.slot_id,
            "distance_cm": distance_cm,
            "is_occupied": classified_occupied,
            "echo_time_us": echo_us
        }


class ParkingLotSimulator:
    def __init__(self, num_slots: int = 6):
        self.sensors = [UltrasonicSensorSimulator(slot_id=i + 1) for i in range(num_slots)]

    def step(self) -> List[Dict]:
        """Simulate random vehicle arrival and departure events."""
        for sensor in self.sensors:
            if not sensor.is_occupied:
                # 15% chance a car parks in an empty space
                if random.random() < 0.15:
                    sensor.is_occupied = True
            else:
                # 10% chance a parked car departs
                if random.random() < 0.10:
                    sensor.is_occupied = False

        # Generate telemetry readings from all 6 sensors
        return [sensor.measure() for sensor in self.sensors]

    def send_telemetry(self, endpoint_url: str = API_TELEMETRY_URL) -> bool:
        """Sends simulated sensor batch to FastAPI backend."""
        readings = self.step()
        payload = {
            "readings": readings,
            "device_id": "SIMULATED_STM32_ESP8266",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        try:
            resp = requests.post(endpoint_url, json=payload, timeout=3.0)
            if resp.status_code == 200:
                occupied_count = sum(1 for r in readings if r["is_occupied"])
                free_count = 6 - occupied_count
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Ingested batch: "
                      f"{occupied_count} Occupied | {free_count} Free slots. "
                      f"Slots: {[r['is_occupied'] for r in readings]}")
                return True
            else:
                print(f"[!] Server responded with status {resp.status_code}: {resp.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"[!] Connection failed to {endpoint_url}: {e}")
            return False


def run_continuous_simulation(interval_seconds: float = 3.0, endpoint_url: str = API_TELEMETRY_URL):
    """Runs a loop posting sensor readings at the specified interval."""
    sim = ParkingLotSimulator(num_slots=6)
    print(f"[*] Starting HC-SR04 parking simulator...")
    print(f"[*] Target backend: {endpoint_url}")
    print(f"[*] Telemetry update interval: {interval_seconds} seconds")
    print(f"[*] Press Ctrl+C to stop simulation.\n")

    try:
        while True:
            sim.send_telemetry(endpoint_url=endpoint_url)
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n[*] Simulator stopped by user.")


def seed_database_with_history(n_batches: int = 40, endpoint_url: str = API_TELEMETRY_URL):
    """Quickly pre-populates the database with n batches of readings."""
    sim = ParkingLotSimulator(num_slots=6)
    print(f"[*] Seeding database with {n_batches} historical snapshots...")
    success_count = 0
    for _ in range(n_batches):
        if sim.send_telemetry(endpoint_url=endpoint_url):
            success_count += 1
        time.sleep(0.05)
    print(f"[+] Seeding complete! {success_count}/{n_batches} batches ingested.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Parking Sensor Simulator")
    parser.add_argument("--mode", choices=["live", "seed", "single"], default="live",
                        help="live: run continuous loop; seed: inject history; single: send 1 batch")
    parser.add_argument("--interval", type=float, default=3.0,
                        help="Telemetry interval in seconds for live mode")
    parser.add_argument("--url", type=str, default=API_TELEMETRY_URL,
                        help="Backend ingestion URL")
    args = parser.parse_args()

    if args.mode == "live":
        run_continuous_simulation(interval_seconds=args.interval, endpoint_url=args.url)
    elif args.mode == "seed":
        seed_database_with_history(n_batches=40, endpoint_url=args.url)
    elif args.mode == "single":
        sim = ParkingLotSimulator(num_slots=6)
        sim.send_telemetry(endpoint_url=args.url)
