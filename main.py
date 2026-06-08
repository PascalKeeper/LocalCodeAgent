"""LocalCodeAgent v2.7 entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from colorama import Fore, Style, init

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.core import LocalCodeAgent  # noqa: E402
from utils.config import load_config  # noqa: E402

init(autoreset=True)


def main() -> int:
    config = load_config()
    version = config.get("version", "2.7.0")
    print(f"{Fore.CYAN}=== LocalCodeAgent v{version} — Director Mode ==={Style.RESET_ALL}")

    try:
        agent = LocalCodeAgent()
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"{Fore.RED}[STARTUP ERROR] {exc}{Style.RESET_ALL}")
        print(
            f"{Fore.YELLOW}Install dependencies: pip install -r requirements.txt{Style.RESET_ALL}"
        )
        print(
            f"{Fore.YELLOW}Place a GGUF model in: {config['paths']['models']}{Style.RESET_ALL}"
        )
        return 1

    while True:
        try:
            cmd = input(f"{Fore.MAGENTA}Director > {Style.RESET_ALL}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Fore.YELLOW}Goodbye.{Style.RESET_ALL}")
            return 0

        if cmd.lower() in {"exit", "quit"}:
            print(f"{Fore.YELLOW}Goodbye.{Style.RESET_ALL}")
            return 0

        if cmd:
            response = agent.chat(cmd)
            print(f"{Fore.CYAN}Agent > {Style.RESET_ALL}{response}\n")


if __name__ == "__main__":
    raise SystemExit(main())
