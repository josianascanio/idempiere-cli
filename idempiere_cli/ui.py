from __future__ import annotations

from rich.console import Console

console = Console()

BANNER = r"""
  _     _                       _                        _ _
 (_)   | |                     (_)                      | (_)
  _  __| | ___ _ __ ___  _ __   _  ___ _ __ ___    ___| |_
 | |/ _` |/ _ \ '_ ` _ \| '_ \ | |/ _ \ '__/ _ \  / __| | |
 | | (_| |  __/ | | | | | |_) || |  __/ | |  __/ | (__| | |
 |_|\__,_|\___|_| |_| |_| .__/ |_|\___|_|  \___|  \___|_|_|
                        | |
                        |_|    Developer CLI for iDempiere
"""


def print_banner() -> None:
    console.print(BANNER, style="bold cyan")
