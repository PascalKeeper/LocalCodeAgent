"""Parse LLM output blocks and persist via safe versioning."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from colorama import Fore, Style

from utils.logger import setup_logger
from utils.versioning import get_versioned_path

_FILE_MARKER = re.compile(r"^(?://|#)\s*File:\s*(.+)$", re.IGNORECASE)


class FileWriter:
    def __init__(self, config: dict[str, Any], log_dir: Path) -> None:
        self._projects_dir = Path(config["paths"]["projects"])
        self._versioning = bool(config["safety"]["versioning_enabled"])
        self._logger = setup_logger(__name__, log_dir)
        self._projects_dir.mkdir(parents=True, exist_ok=True)

    def save_from_response(self, response: str) -> list[Path]:
        saved: list[Path] = []
        current_file: Path | None = None
        code_buffer: list[str] = []
        in_block = False

        for line in response.splitlines():
            marker = _FILE_MARKER.match(line.strip())
            if marker:
                current_file = self._projects_dir / marker.group(1).strip()
                code_buffer = []
                print(f"{Fore.CYAN}→ Preparing: {marker.group(1).strip()}{Style.RESET_ALL}")
                continue

            if line.strip().startswith("```"):
                if in_block and current_file and code_buffer:
                    saved_path = self._write_file(current_file, "\n".join(code_buffer))
                    if saved_path:
                        saved.append(saved_path)
                    current_file = None
                in_block = not in_block
                code_buffer = []
                continue

            if in_block and current_file is not None:
                code_buffer.append(line)

        if in_block and current_file and code_buffer:
            saved_path = self._write_file(current_file, "\n".join(code_buffer))
            if saved_path:
                saved.append(saved_path)

        return saved

    def _write_file(self, filepath: Path, content: str) -> Path | None:
        try:
            final_path = get_versioned_path(filepath) if self._versioning else filepath
            final_path.parent.mkdir(parents=True, exist_ok=True)
            final_path.write_text(content, encoding="utf-8")

            if final_path != filepath:
                print(
                    f"{Fore.YELLOW}[VERSIONED] Original exists → {final_path.name}{Style.RESET_ALL}"
                )
            else:
                rel = final_path.relative_to(self._projects_dir.parent)
                print(f"{Fore.GREEN}[SUCCESS] Saved → {rel}{Style.RESET_ALL}")

            self._logger.info("Wrote file: %s", final_path)
            return final_path
        except OSError as exc:
            print(f"{Fore.RED}[ERROR] {exc}{Style.RESET_ALL}")
            self._logger.error("Write failed for %s: %s", filepath, exc)
            return None
