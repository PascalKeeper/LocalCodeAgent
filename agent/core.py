"""LocalCodeAgent v2.7 orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from colorama import Fore, Style, init

from agent.self_debug import SelfDebugger
from utils.config import load_config
from utils.file_writer import FileWriter
from utils.llm_engine import LLMEngine
from utils.logger import setup_logger
from utils.rag_engine import RAGEngine
from utils.scanner import CodeScanner

init(autoreset=True)


class LocalCodeAgent:
    def __init__(self, config_path: Path | None = None) -> None:
        self._config = load_config(config_path)
        paths = self._config["paths"]
        self._log_dir = Path(paths["logs"])
        self._prompts_dir = Path(paths["agent_root"]) / "prompts"

        for directory in (self._log_dir, Path(paths["projects"]), Path(paths["models"])):
            directory.mkdir(parents=True, exist_ok=True)

        self._logger = setup_logger(__name__, self._log_dir)
        self._system_prompt = (self._prompts_dir / "system_director.txt").read_text(
            encoding="utf-8"
        )

        self._scanner = CodeScanner(self._config, self._log_dir)
        self._code_index = self._scanner.build_index()

        self._rag = RAGEngine(self._config, self._log_dir)
        self._rag.ingest_code_index(self._code_index)
        self._rag.ingest_pdfs()

        self._llm: LLMEngine | None = None
        self._debugger: SelfDebugger | None = None
        self._writer = FileWriter(self._config, self._log_dir)

        print(
            f"{Fore.GREEN}LocalCodeAgent v{self._config['version']} ready "
            f"| indexed {len(self._code_index)} files{Style.RESET_ALL}"
        )

    @property
    def config(self) -> dict[str, Any]:
        return self._config

    def _ensure_llm(self) -> tuple[LLMEngine, SelfDebugger]:
        if self._llm is None:
            self._llm = LLMEngine(self._config, self._log_dir)
            self._debugger = SelfDebugger(self._config, self._llm, self._log_dir)
        return self._llm, self._debugger  # type: ignore[return-value]

    def chat(self, prompt: str) -> str:
        print(f"{Fore.CYAN}Processing with safe versioning...{Style.RESET_ALL}")
        context_parts = [
            f"Indexed files: {len(self._code_index)}",
            f"Hardware: {self._config['hardware']['gpu_name']} "
            f"({self._config['hardware']['vram_mb']} MB VRAM)",
        ]

        rag_context = self._rag.query(prompt)
        if rag_context:
            context_parts.append(f"RAG context:\n{rag_context}")

        sample_paths = list(self._code_index.keys())[:8]
        if sample_paths:
            context_parts.append("Sample indexed paths:\n" + "\n".join(sample_paths))

        user_prompt = (
            "\n\n".join(context_parts)
            + "\n\nDirector request:\n"
            + prompt
            + "\n\nWhen writing files, use this format:\n"
            + "// File: relative/path/from/Projects\n"
            + "```python\n# code\n```"
        )

        llm, debugger = self._ensure_llm()
        response = llm.generate(self._system_prompt, user_prompt)
        reviewed, status = debugger.review(prompt, response)
        final_response = reviewed if status == "REVISED" else response

        saved = self._writer.save_from_response(final_response)
        footer = (
            f"\n\nSelf-Debug Review: status={status} | saved_files={len(saved)}"
        )
        self._logger.info("Chat complete | status=%s | saved=%d", status, len(saved))
        return final_response + footer
