"""
Watch mode loop for NetCheck CLI.

Decoupled from all CLI state — accepts any callable that executes one
check cycle and returns a bool (True = all passed).
"""
import os
import sys
import time
import platform
from datetime import datetime
from typing import Callable


def _clear_screen() -> None:
    """Clear terminal screen cross-platform."""
    if platform.system().lower() == "windows":
        os.system("cls")
    else:
        os.system("clear")


def run_watch_loop(execute_fn: Callable[[], bool], interval: float) -> None:
    """
    Loop indefinitely, calling execute_fn every `interval` seconds.

    Clears the screen before each run and shows a timestamp header.
    Exits cleanly on KeyboardInterrupt (Ctrl+C) with exit code 0.
    """
    from netcheck.cli.exitcodes import EXIT_OK
    try:
        while True:
            _clear_screen()
            print(
                f"NetCheck Watch Mode — Interval: {interval}s — "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            execute_fn()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nWatch mode stopped.")
        sys.exit(EXIT_OK)
