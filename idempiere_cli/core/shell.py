from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from idempiere_cli.core.logger import setup_logging

console = Console()
logger = setup_logging()


@dataclass
class CommandResult:
    command: str
    stdout: str
    stderr: str
    returncode: int
    duration: float
    dry_run: bool = False


def command_exists(command: str) -> bool:
    return subprocess.run(["sh", "-c", f"command -v {shlex.quote(command)} >/dev/null 2>&1"]).returncode == 0


def run_command(
    command: str | list[str],
    dry_run: bool = False,
    check: bool = True,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    stream: bool = False,
) -> CommandResult:
    command_display = command if isinstance(command, str) else " ".join(shlex.quote(part) for part in command)
    if dry_run:
        console.print(f"[yellow]DRY-RUN:[/yellow] {command_display}")
        logger.info("DRY-RUN %s", command_display)
        return CommandResult(str(command_display), "", "", 0, 0.0, True)

    start = time.monotonic()
    logger.info("RUN %s", command_display)
    if stream:
        console.print(f"[cyan]$[/cyan] {command_display}")
        process = subprocess.Popen(
            command,
            cwd=str(cwd) if cwd else None,
            env={**os.environ, **env} if env else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=isinstance(command, str),
            bufsize=1,
        )
        output_lines: list[str] = []
        assert process.stdout is not None
        for line in process.stdout:
            output_lines.append(line)
            console.print(line.rstrip())
        returncode = process.wait()
        duration = time.monotonic() - start
        stdout = "".join(output_lines)
        logger.info("EXIT %s code=%s duration=%.2fs", command_display, returncode, duration)
        if stdout:
            logger.info("OUTPUT %s", stdout.strip())
        if check and returncode != 0:
            raise RuntimeError(f"Comando falló ({returncode}): {command_display}\n{stdout}")
        return CommandResult(str(command_display), stdout, "", returncode, duration)

    process = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env={**os.environ, **env} if env else None,
        text=True,
        capture_output=True,
        shell=isinstance(command, str),
    )
    duration = time.monotonic() - start
    logger.info("EXIT %s code=%s duration=%.2fs", command_display, process.returncode, duration)
    if process.stdout:
        logger.info("STDOUT %s", process.stdout.strip())
    if process.stderr:
        logger.info("STDERR %s", process.stderr.strip())
    if check and process.returncode != 0:
        raise RuntimeError(f"Comando falló ({process.returncode}): {command_display}\n{process.stderr}")
    return CommandResult(str(command_display), process.stdout, process.stderr, process.returncode, duration)


def sudo_command(parts: list[str]) -> list[str]:
    if os.geteuid() == 0:
        return parts
    if command_exists("sudo"):
        return ["sudo", *parts]
    return parts
