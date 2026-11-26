"""Start Streamlit, verify its health endpoint, and stop the temporary server."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

root = Path(__file__).resolve().parents[1]
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py",
    "--server.headless=true", "--server.address=127.0.0.1", f"--server.port={port}"],
    cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
try:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Streamlit exited early: {process.returncode}")
        try:
            with urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=2) as response:
                assert response.status == 200
                print("Streamlit HTTP health check passed.")
                break
        except OSError:
            time.sleep(0.5)
    else:
        raise TimeoutError("Streamlit did not become healthy within 45 seconds.")
finally:
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
