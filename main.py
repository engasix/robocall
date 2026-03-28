"""
Robocall — Project Entry Point
Starts all services (API, Demo, and future components) as subprocesses.

Usage:
    uv run main.py
"""

import subprocess
import sys
import signal
import os

SERVICES = [
    {
        "name": "API",
        "cmd": ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"],
    },
    {
        "name": "Demo",
        "cmd": ["uvicorn", "demo.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
    },
    # Future components:
    # {"name": "Dashboard", "cmd": ["uvicorn", "dashboard.main:app", "--port", "8002", "--reload"]},
    # {"name": "Scheduler", "cmd": ["python", "-m", "scheduler.main"]},
]


def main():
    processes = []

    for service in SERVICES:
        print(f"  Starting {service['name']}...")
        proc = subprocess.Popen(
            service["cmd"],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        processes.append((service["name"], proc))

    print(f"\n  All services running. Press Ctrl+C to stop.\n")

    def shutdown(sig, frame):
        print("\n  Shutting down all services...")
        for name, proc in processes:
            proc.terminate()
            print(f"  Stopped {name}")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    for name, proc in processes:
        proc.wait()


if __name__ == "__main__":
    main()
