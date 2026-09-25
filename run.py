import os
import subprocess
import sys
from pathlib import Path

def run():
    # Set PYTHONPATH to the current directory so 'backend' is treat as a package
    # but also allow running from within 'backend' if needed.
    # For this setup, we run from the project root.
    root_dir = Path(__file__).parent.absolute()
    os.environ["PYTHONPATH"] = str(root_dir)

    print("🚀 Starting ASEP Backend Services...")

    # API Server
    api_cmd = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--port", "8000"]

    # Celery Worker
    # We use the full path to the app.celery_app
    worker_cmd = [sys.executable, "-m", "celery", "-A", "backend.app.celery_app", "worker", "--loglevel=info"]

    try:
        api_process = subprocess.Popen(api_cmd, stdout=None, stderr=None)
        print("✅ API Server started on http://127.0.0.1:8000")

        worker_process = subprocess.Popen(worker_cmd, stdout=None, stderr=None)
        print("✅ Celery Worker started")

        print("\nPress Ctrl+C to stop all services.")
        api_process.wait()
        worker_process.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        api_process.terminate()
        worker_process.terminate()
        print("Stopped.")

if __name__ == "__main__":
    run()
