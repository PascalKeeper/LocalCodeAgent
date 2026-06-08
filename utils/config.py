"""Configuration loader with path normalization for Windows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONFIG_CACHE: dict[str, Any] | None = None


def _agent_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None and config_path is None:
        return _CONFIG_CACHE

    root = _agent_root()
    path = config_path or (root / "config.json")
    with open(path, encoding="utf-8") as handle:
        config: dict[str, Any] = json.load(handle)

    paths = config.setdefault("paths", {})
    for key, value in list(paths.items()):
        if isinstance(value, str):
            paths[key] = str(Path(value))
        elif isinstance(value, list):
            paths[key] = [str(Path(item)) for item in value]

    config["paths"]["agent_root"] = str(root)
    _CONFIG_CACHE = config
    return config
