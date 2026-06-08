# LocalCodeAgent v2.7

Offline, hardware-aware local coding agent for Project Director workflows. Runs entirely on local hardware with safe file versioning, code scanning, llama.cpp inference, and Chroma RAG over PDF manuals.

**Target hardware:** NVIDIA GTX 1070 (8 GB VRAM), 32 GB RAM, Windows 10.

## Features

- **Safe versioning** — never overwrites existing files; writes `_v2`, `_v3`, etc.
- **Code scanner** — indexes configured roots on `F:/imonlinegaming`
- **llama.cpp GGUF** — quantized local LLM with GPU layer offload tuned for 8 GB VRAM
- **RAG** — Chroma persistent index over scanned code and CodersGuild PDFs
- **Self-debug loop** — second-pass LLM review before saving generated files
- **Config-driven paths** — all directories and hardware knobs in `config.json`

## Quick Start

**Double-click (recommended):**
- `CONTINUE_SHIP.bat` — menu: CUDA install, CPU install, base deps, verify
- `INSTALL_DEPS.bat` — one-click CUDA install for GTX 1070

**PowerShell:**
```powershell
cd F:\imonlinegaming\LocalCodeAgent
.\scripts\install_deps.ps1 -Cuda      # GPU (recommended)
.\scripts\install_deps.ps1 -CpuOnly   # CPU llama-cpp
.\scripts\install_deps.ps1 -SkipLlm   # RAG/scanner deps only
.\scripts\verify_deps.ps1             # verify only
```

1. Place a quantized GGUF model in `models/` (Q4_K_M recommended).
2. Update `config.json` → `llm.model_filename` if needed.
3. Run:

```powershell
python main.py
```

## Build EXE

```powershell
pip install pyinstaller
pyinstaller LocalCodeAgent.spec
```

Output: `dist/LocalCodeAgent.exe`

## Project Layout

```
LocalCodeAgent/
├── main.py              # Entry point
├── config.json          # Paths, hardware, LLM, RAG settings
├── agent/               # Orchestrator + self-debug
├── utils/               # Scanner, LLM, RAG, versioning, file writer
├── prompts/             # System and review prompts
├── Projects/            # Versioned output (Director deliverables)
├── models/              # GGUF models (not committed)
├── RAG_Index/           # Chroma DB (not committed)
└── logs/                # Rotating logs
```

## Safety Rules

- Original user files are never modified.
- Generated files land in `Projects/` via `// File:` markers in LLM output.
- If a target exists, `_vN` suffix is applied automatically.

## License

MIT — see [LICENSE](LICENSE).

## Author

Joseph Rocco Peransi ([@pascalkeeper](https://github.com/pascalkeeper))
