"""Safe file versioning — never overwrite existing user files."""

from __future__ import annotations

from pathlib import Path


def get_versioned_path(filepath: Path) -> Path:
    """Return filepath if absent, else the next available _vN suffixed path."""
    if not filepath.exists():
        return filepath

    stem = filepath.stem
    suffix = filepath.suffix
    parent = filepath.parent
    version = 2
    while True:
        candidate = parent / f"{stem}_v{version}{suffix}"
        if not candidate.exists():
            return candidate
        version += 1
