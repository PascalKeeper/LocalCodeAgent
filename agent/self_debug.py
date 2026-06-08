"""Second-pass LLM review for generated code quality and safety."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.llm_engine import LLMEngine
from utils.logger import setup_logger


class SelfDebugger:
    def __init__(self, config: dict[str, Any], llm: LLMEngine, log_dir: Path) -> None:
        self._config = config
        self._llm = llm
        self._enabled = bool(config["safety"]["self_debug_enabled"])
        self._logger = setup_logger(__name__, log_dir)
        self._review_prompt = (
            Path(config["paths"]["agent_root"]) / "prompts" / "self_debug_review.txt"
        ).read_text(encoding="utf-8")

    def review(self, original_prompt: str, generated: str) -> tuple[str, str]:
        if not self._enabled:
            return generated, "SKIPPED"

        review_input = (
            f"Director request:\n{original_prompt}\n\n"
            f"Generated output:\n{generated}\n\n"
            "Review for bugs, edge cases, GTX 1070 compatibility, "
            "Windows path safety, and versioning compliance."
        )
        reviewed = self._llm.generate(self._review_prompt, review_input).strip()
        upper = reviewed.upper()
        if upper.startswith("APPROVED"):
            status = "APPROVED"
            cleaned = reviewed.split("\n", 1)[1].strip() if "\n" in reviewed else generated
            return cleaned or generated, status

        status = "REVISED"
        cleaned = reviewed
        if upper.startswith("REVISED") and "\n" in reviewed:
            cleaned = reviewed.split("\n", 1)[1].strip()
        self._logger.info("Self-debug status: %s", status)
        return cleaned, status
