from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from idempiere_cli.core.config import default_profile, derive_profile_values, load_profile
from idempiere_cli.core.dependencies import detect_dependencies
from idempiere_cli.core.detection import detect_architecture, detect_os
from idempiere_cli.core.java import validate_java_for_idempiere
from idempiere_cli.core.ports import validate_required_ports
from idempiere_cli.core.postgres import validate_postgres
from idempiere_cli.core.resources import ValidationResult, validate_disk, validate_ram
from idempiere_cli.core.shell import command_exists

console = Console()


def _style(status: str) -> str:
    return {"OK": "green", "WARNING": "yellow", "ERROR": "red"}.get(status, "white")


def collect_checks(profile: dict, installer: str | None = None) -> list[ValidationResult]:
    profile = derive_profile_values(profile)
    results: list[ValidationResult] = []
    os_name = detect_os()
    results.append(ValidationResult("Sistema operativo", "OK" if os_name == "Linux" else "WARNING", os_name))
    arch = detect_architecture()
    results.append(ValidationResult("Arquitectura", "OK" if arch in {"x86_64", "amd64", "aarch64", "arm64"} else "ERROR", arch))
    results.append(validate_ram(profile["resources"]["min_ram_gb"], profile["resources"]["recommended_ram_gb"]))
    results.append(validate_disk(profile["resources"]["disk_check_path"], profile["resources"]["min_disk_gb"], profile["resources"]["recommended_disk_gb"]))
    results.append(validate_postgres(13))
    results.append(validate_java_for_idempiere(int(profile["version"])))
    ports = profile["ports"]
    results.extend(validate_required_ports(ports["web"], ports["ssl"], ports["shutdown"], profile["database"].get("port")))
    results.append(ValidationResult("Nginx", "OK" if command_exists("nginx") else "WARNING", "instalado" if command_exists("nginx") else "no instalado"))
    base_dir = Path(profile["base_dir"])
    if base_dir.exists():
        writable = base_dir.is_dir()
        results.append(ValidationResult("Directorio base", "OK" if writable else "ERROR", str(base_dir)))
    else:
        results.append(ValidationResult("Directorio base", "WARNING", f"No existe todavía: {base_dir}"))
    for dep in detect_dependencies(profile["java"].get("required_version", 17), profile["database"].get("version", 15), profile.get("nginx", {}).get("enabled", False)):
        status = "OK" if dep.installed else ("ERROR" if dep.required else "WARNING")
        results.append(ValidationResult(f"Comando {dep.command}", status, "instalado" if dep.installed else f"falta paquete {dep.package}"))
    if installer:
        results.append(ValidationResult("Instalador solicitado", "OK", installer))
    return results


def print_checks(results: list[ValidationResult]) -> None:
    table = Table(title="Validaciones del servidor")
    table.add_column("Estado")
    table.add_column("Validación", style="cyan")
    table.add_column("Detalle")
    for result in results:
        table.add_row(f"[{_style(result.status)}]{result.status}[/{_style(result.status)}]", result.name, result.message)
    console.print(table)


def check_command(
    profile: Path | None = typer.Option(None, "--profile", "-p", help="Perfil YAML a validar."),
    target_version: int = typer.Option(12, "--target-version", help="Versión iDempiere objetivo."),
    installer: str | None = typer.Option(None, "--installer", help="Instalador objetivo: 12-x86, 12-arm o 12-debian."),
) -> None:
    data = load_profile(profile) if profile else default_profile(target_version)
    results = collect_checks(data, installer)
    print_checks(results)
    if any(result.status == "ERROR" for result in results):
        raise typer.Exit(code=1)
