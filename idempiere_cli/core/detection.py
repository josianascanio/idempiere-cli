from __future__ import annotations

import platform
import subprocess
from pathlib import Path

from idempiere_cli.core.resources import get_available_ram_gb, get_disk_free_gb, get_total_ram_gb
from idempiere_cli.core.shell import command_exists


def detect_os() -> str:
    return platform.system()


def _os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value.strip().strip('"')
    return data


def detect_distribution() -> dict[str, str]:
    data = _os_release()
    return {
        "id": data.get("ID", "unknown"),
        "name": data.get("PRETTY_NAME", data.get("NAME", "unknown")),
        "version": data.get("VERSION_ID", "unknown"),
        "codename": data.get("VERSION_CODENAME", ""),
    }


def detect_architecture() -> str:
    return platform.machine().lower()


def detect_kernel() -> str:
    return platform.release()


def detect_cpu() -> str:
    if command_exists("lscpu"):
        result = subprocess.run(["lscpu"], text=True, capture_output=True)
        for line in result.stdout.splitlines():
            if line.startswith("Model name:"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def detect_installer() -> tuple[str | None, str]:
    distro = detect_distribution()["id"].lower()
    arch = detect_architecture()
    if arch in {"aarch64", "arm64"}:
        return "12-arm", "Arquitectura ARM/aarch64 detectada"
    if distro == "debian":
        return "12-debian", "Debian puro detectado"
    if arch in {"x86_64", "amd64"} and distro in {"ubuntu", "debian", "linuxmint", "pop"}:
        return "12-x86", "Arquitectura x86_64 compatible detectada"
    return None, "No se pudo seleccionar instalador automáticamente"


def detect_environment_summary(disk_path: str = "/opt") -> dict[str, object]:
    distro = detect_distribution()
    installer, reason = detect_installer()
    return {
        "os": detect_os(),
        "distribution": distro["name"],
        "distribution_id": distro["id"],
        "distribution_version": distro["version"],
        "architecture": detect_architecture(),
        "kernel": detect_kernel(),
        "cpu": detect_cpu(),
        "ram_total_gb": get_total_ram_gb(),
        "ram_available_gb": get_available_ram_gb(),
        "disk_path": disk_path,
        "disk_free_gb": get_disk_free_gb(disk_path) if Path(disk_path).exists() else None,
        "recommended_installer": installer,
        "installer_reason": reason,
    }
