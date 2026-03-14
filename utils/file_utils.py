"""File and path utilities."""
import os
import tempfile
from pathlib import Path
from typing import Optional


def make_safe_temp_copy(original_path: str, suffix: Optional[str] = None) -> str:
    """Create a temporary copy of a file's bytes to avoid problems with odd filenames.

    Returns the path to the temp copy (caller should delete when done).
    """
    with open(original_path, "rb") as src:
        data = src.read()
    ext = suffix or os.path.splitext(original_path)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp_name = tmp.name
    tmp.close()
    with open(tmp_name, "wb") as f:
        f.write(data)
    return tmp_name


def ensure_dir(path: str | Path) -> Path:
    """Ensure directory exists; return Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
