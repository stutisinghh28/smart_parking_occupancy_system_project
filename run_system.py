"""
Convenience launcher for the Smart Parking Occupancy Predictor system.
Allows launching the FastAPI backend, Streamlit dashboard, or sensor simulator with simple flags.
"""

import sys
import subprocess
import argparse
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def run_backend(port: int = 8000, reload: bool = True):
    print(f"[*] Starting FastAPI backend on http://127.0.0.1:{port} ...")
    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", str(port)
    ]
    if reload:
        cmd.append("--reload")
    subprocess.run(cmd, cwd=PROJECT_ROOT)


def run_dashboard(port: int = 8501):
    print(f"[*] Starting Streamlit Dashboard on http://localhost:{port} ...")
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        os.path.join(PROJECT_ROOT, "frontend", "dashboard.py"),
        "--server.port", str(port),
        "--server.headless", "true"
    ]
    subprocess.run(cmd, cwd=PROJECT_ROOT)


def run_simulator(mode: str = "live", interval: float = 3.0):
    print(f"[*] Starting Ultrasonic Sensor Simulator (mode={mode}) ...")
    cmd = [
        sys.executable,
        os.path.join(PROJECT_ROOT, "simulator", "simulate_parking.py"),
        "--mode", mode,
        "--interval", str(interval)
    ]
    subprocess.run(cmd, cwd=PROJECT_ROOT)


def run_all():
    print("[*] Launching Backend and Streamlit Dashboard concurrently...")
    p1 = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ], cwd=PROJECT_ROOT)

    p2 = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run",
        os.path.join(PROJECT_ROOT, "frontend", "dashboard.py"),
        "--server.port", "8501"
    ], cwd=PROJECT_ROOT)

    try:
        p1.wait()
        p2.wait()
    except KeyboardInterrupt:
        print("\n[*] Terminating all processes...")
        p1.terminate()
        p2.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Parking Launcher")
    parser.add_argument("--backend", action="store_true", help="Launch FastAPI backend")
    parser.add_argument("--dashboard", action="store_true", help="Launch Streamlit dashboard")
    parser.add_argument("--simulate", action="store_true", help="Run live sensor simulator")
    parser.add_argument("--seed", action="store_true", help="Seed database with historical data")
    parser.add_argument("--all", action="store_true", help="Launch backend + dashboard together")

    args = parser.parse_args()

    if args.backend:
        run_backend()
    elif args.dashboard:
        run_dashboard()
    elif args.simulate:
        run_simulator(mode="live")
    elif args.seed:
        run_simulator(mode="seed")
    elif args.all:
        run_all()
    else:
        parser.print_help()
