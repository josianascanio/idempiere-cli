from __future__ import annotations

import re
import subprocess
from pathlib import Path

from idempiere_cli.core.resources import ValidationResult
from idempiere_cli.core.shell import command_exists


def get_java_version() -> str | None:
    if not command_exists("java"):
        return None
    result = subprocess.run(["java", "-version"], text=True, capture_output=True)
    output = result.stderr or result.stdout
    first = output.splitlines()[0] if output else ""
    match = re.search(r'"([^"]+)"', first)
    return match.group(1) if match else first.strip() or None


def _major(version: str | None) -> int | None:
    if not version:
        return None
    if version.startswith("1."):
        parts = version.split(".")
        return int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    match = re.match(r"(\d+)", version)
    return int(match.group(1)) if match else None


def get_installed_javas() -> list[str]:
    candidates: list[str] = []
    for root in [Path("/usr/lib/jvm"), Path("/Library/Java/JavaVirtualMachines")]:
        if root.exists():
            candidates.extend(str(path) for path in sorted(root.iterdir()) if path.is_dir())
    version = get_java_version()
    if version:
        candidates.insert(0, f"java en PATH: {version}")
    return candidates


def validate_java_for_idempiere(version: int) -> ValidationResult:
    required = 17 if version >= 12 else 11
    detected = get_java_version()
    major = _major(detected)
    if major is None:
        return ValidationResult("Java", "ERROR", f"Java {required} requerido, no detectado")
    if major != required:
        return ValidationResult("Java", "WARNING", f"Detectado Java {major}, requerido Java {required} para iDempiere {version}")
    return ValidationResult("Java", "OK", f"Java {detected}")


def find_java_home(required_version: int) -> str | None:
    for path in get_installed_javas():
        if str(required_version) in path:
            return path
    return None
