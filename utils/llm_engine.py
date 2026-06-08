"""llama.cpp GGUF inference tuned for GTX 1070 (8 GB VRAM)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.logger import setup_logger

try:
    from llama_cpp import Llama
except ImportError as exc:
    Llama = None  # type: ignore[misc, assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class LLMEngine:
    def __init__(self, config: dict[str, Any], log_dir: Path) -> None:
        if Llama is None:
            raise RuntimeError(
                "llama-cpp-python is not installed. "
                "Run: pip install llama-cpp-python"
            ) from _IMPORT_ERROR

        self._config = config
        self._logger = setup_logger(__name__, log_dir)
        self._llm_cfg = config["llm"]
        self._hw = config["hardware"]
        self._model_path = Path(config["paths"]["models"]) / self._llm_cfg["model_filename"]
        self._model: Llama | None = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        if not self._model_path.exists():
            raise FileNotFoundError(
                f"GGUF model not found: {self._model_path}. "
                "Place a quantized model (Q4_K_M recommended) in the models directory."
            )

        self._logger.info("Loading model: %s", self._model_path.name)
        self._model = Llama(
            model_path=str(self._model_path),
            n_ctx=int(self._hw["n_ctx"]),
            n_gpu_layers=int(self._hw["n_gpu_layers"]),
            n_threads=int(self._hw["n_threads"]),
            n_batch=int(self._hw["n_batch"]),
            verbose=False,
        )
        self._logger.info(
            "Model ready | GPU layers=%s | ctx=%s",
            self._hw["n_gpu_layers"],
            self._hw["n_ctx"],
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self._model is None:
            self.load()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        result = self._model.create_chat_completion(
            messages=messages,
            temperature=float(self._llm_cfg["temperature"]),
            max_tokens=int(self._llm_cfg["max_tokens"]),
            top_p=float(self._llm_cfg["top_p"]),
            repeat_penalty=float(self._llm_cfg["repeat_penalty"]),
        )
        return result["choices"][0]["message"]["content"].strip()
