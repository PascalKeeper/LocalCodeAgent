"""Filesystem code indexer scoped to configured roots."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from utils.logger import setup_logger


class CodeScanner:
    def __init__(self, config: dict[str, Any], log_dir: Path) -> None:
        self._config = config
        self._logger = setup_logger(__name__, log_dir)
        scanner_cfg = config["scanner"]
        self._skip_dirs = set(scanner_cfg["skip_dirs"])
        self._extensions = {ext.lower() for ext in scanner_cfg["allowed_extensions"]}
        self._max_bytes = int(scanner_cfg["max_file_bytes"])
        self._preview_chars = int(scanner_cfg["content_preview_chars"])
        self._max_files = int(scanner_cfg.get("max_files", 2000))
        self._roots = [Path(p) for p in config["paths"]["scan_roots"]]

    def build_index(self) -> dict[str, str]:
        index: dict[str, str] = {}
        for root in self._roots:
            if not root.exists():
                self._logger.warning("Scan root missing: %s", root)
                continue
            self._walk_root(root, index)
            if len(index) >= self._max_files:
                break
        self._logger.info("Indexed %d files", len(index))
        return index

    def _walk_root(self, root: Path, index: dict[str, str]) -> None:
        if len(index) >= self._max_files:
            return
        agent_root = Path(self._config["paths"]["agent_root"])
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in self._skip_dirs]
            current = Path(dirpath)
            if agent_root in current.parents or current == agent_root:
                continue
            for filename in filenames:
                if len(index) >= self._max_files:
                    return
                path = current / filename
                if path.suffix.lower() not in self._extensions:
                    continue
                try:
                    if path.stat().st_size > self._max_bytes:
                        continue
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    index[str(path)] = content[: self._preview_chars]
                except OSError as exc:
                    self._logger.debug("Skipped %s: %s", path, exc)
