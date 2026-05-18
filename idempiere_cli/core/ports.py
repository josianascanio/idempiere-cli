from __future__ import annotations

import socket
import subprocess

from idempiere_cli.core.resources import ValidationResult
from idempiere_cli.core.shell import command_exists


def is_port_in_use(port: int, host: str = "0.0.0.0") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def get_listening_ports() -> list[str]:
    if command_exists("ss"):
        result = subprocess.run(["ss", "-tulpn"], text=True, capture_output=True)
        return result.stdout.splitlines()
    return []


def validate_required_ports(web: int, ssl: int, db: int | None = None) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for name, port in [("Web", web), ("SSL", ssl)]:
        if is_port_in_use(port):
            results.append(ValidationResult(f"Puerto {name}", "ERROR", f"{port} ocupado"))
        else:
            results.append(ValidationResult(f"Puerto {name}", "OK", f"{port} libre"))
    if db:
        status = "OK" if is_port_in_use(db) else "WARNING"
        message = f"{db} escuchando" if status == "OK" else f"{db} no parece escuchar localmente"
        results.append(ValidationResult("Puerto PostgreSQL", status, message))
    return results
