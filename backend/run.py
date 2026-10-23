"""Entry point.

Development:  python run.py
Production:   gunicorn run:app  (see docs/deployment.md)
"""
import os
import subprocess
import sys
from pathlib import Path

# If started with the system Python, re-launch with the project's .venv
# so `python run.py` works without activating the venv first.
_VENV = Path(__file__).resolve().parent / ".venv"
_VENV_PY = _VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if __name__ == "__main__" and _VENV_PY.exists() and Path(sys.prefix).resolve() != _VENV.resolve():
    sys.exit(subprocess.call([str(_VENV_PY), *sys.argv]))

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")), debug=app.config["DEBUG"])
