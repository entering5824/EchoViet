"""
Entry point shim for deployments expecting `main.py` at repo root.
Delegates to Streamlit app in `app/main.py`.
"""
import os
import sys

# Ensure project root is on path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import the Streamlit app (executes on import)
import app.main  # noqa: F401

if __name__ == "__main__":
    # When run via `streamlit run main.py`, the import above initializes the app.
    # No further action needed here.
    pass
