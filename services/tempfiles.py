from __future__ import annotations
from pathlib import Path
import tempfile
import os
import time


def safe_save_upload(file_storage, suffix: str) -> Path:
    """Save an uploaded file to a temporary path, closed for Windows safety."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    p = Path(path)
    file_storage.save(p.as_posix())
    return p


def safe_unlink(p: Path, tries: int = 5, delay: float = 0.2) -> None:
    """Attempt to delete a file, retrying on Windows PermissionError."""
    for _ in range(tries):
        try:
            p.unlink(missing_ok=True)
            return
        except PermissionError:
            time.sleep(delay)
