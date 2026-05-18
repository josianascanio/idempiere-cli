from __future__ import annotations

import tempfile
import re
from dataclasses import dataclass
from pathlib import Path

from idempiere_cli.core.detection import detect_distribution
from rich.console import Console

from idempiere_cli.core.shell import command_exists, run_command, sudo_command

console = Console()


BASE_PACKAGES = ["curl", "wget", "unzip", "tar", "fontconfig", "git"]
PACKAGE_LABELS = {
    "openjdk-17-jdk-headless": "Java 17 JDK",
    "postgresql-15": "PostgreSQL 15 server",
    "postgresql-client-15": "PostgreSQL 15 client tools (psql, pg_dump, pg_restore)",
    "fontconfig": "fontconfig (fuentes para reportes/PDF)",
    "unzip": "unzip (extraer build iDempiere)",
    "nginx": "Nginx web server",
}


@dataclass
class Dependency:
    name: str
    command: str
    package: str
    installed: bool
    required: bool = True


def detect_dependencies(java_version: int = 17, postgres_version: int = 15, include_nginx: bool = False) -> list[Dependency]:
    deps = [
        Dependency("curl", "curl", "curl", command_exists("curl")),
        Dependency("wget", "wget", "wget", command_exists("wget")),
        Dependency("unzip", "unzip", "unzip", command_exists("unzip")),
        Dependency("tar", "tar", "tar", command_exists("tar")),
        Dependency("fontconfig", "fc-cache", "fontconfig", command_exists("fc-cache")),
        Dependency("git", "git", "git", command_exists("git")),
    ]
    pg_client_package = f"postgresql-client-{postgres_version}"
    deps.extend(
        [
            Dependency(f"Java {java_version}", "java", f"openjdk-{java_version}-jdk-headless", command_exists("java")),
            Dependency(f"PostgreSQL {postgres_version}", "psql", f"postgresql-{postgres_version}", command_exists("psql")),
            Dependency("psql", "psql", pg_client_package, command_exists("psql")),
            Dependency("pg_dump", "pg_dump", pg_client_package, command_exists("pg_dump")),
            Dependency("pg_restore", "pg_restore", pg_client_package, command_exists("pg_restore")),
            Dependency("systemctl", "systemctl", "systemd", command_exists("systemctl")),
            Dependency("ss", "ss", "iproute2", command_exists("ss")),
        ]
    )
    deps.append(Dependency("Nginx", "nginx", "nginx", command_exists("nginx"), required=include_nginx))
    return deps


def missing_packages(deps: list[Dependency]) -> list[str]:
    packages: list[str] = []
    for dep in deps:
        if not dep.installed and dep.required and dep.package not in packages:
            packages.append(dep.package)
    return packages


def package_label(package: str) -> str:
    return PACKAGE_LABELS.get(package, package)


def format_package_list(packages: list[str]) -> str:
    return ", ".join(package_label(package) for package in packages)


def _run_compact(command: list[str], label: str, dry_run: bool = False) -> None:
    if dry_run:
        run_command(command, dry_run=True)
        return
    with console.status(label, spinner="dots"):
        run_command(command)
    console.print(f"[green]OK[/green] {label}")


def apt_package_available(package: str) -> bool:
    if not command_exists("apt-cache"):
        return False
    result = run_command(["apt-cache", "policy", package], check=False)
    for line in result.stdout.splitlines():
        if line.strip().startswith("Candidate:"):
            return "(none)" not in line and "(ninguno)" not in line
    return False


def selected_postgres_version(packages: list[str]) -> int | None:
    for package in packages:
        match = re.fullmatch(r"postgresql(?:-client)?-(\d+)", package)
        if match:
            return int(match.group(1))
    return None


def configure_postgresql_apt_repo(version: int, dry_run: bool = False) -> None:
    package = f"postgresql-{version}"
    if apt_package_available(package):
        return

    distro = detect_distribution()
    codename = distro.get("codename")
    if not codename:
        result = run_command(["lsb_release", "-cs"], check=False, dry_run=dry_run)
        codename = result.stdout.strip() if result.stdout else ""
    if not codename and not dry_run:
        raise RuntimeError("No se pudo detectar el codename de la distribución para configurar el repo PostgreSQL.")

    _run_compact(sudo_command(["apt", "update", "-y"]), "Actualizando repositorios apt", dry_run=dry_run)
    _run_compact(sudo_command(["apt", "install", "-y", "wget", "ca-certificates", "lsb-release", "gnupg"]), "Instalando herramientas para repo PostgreSQL", dry_run=dry_run)
    _run_compact(sudo_command(["install", "-d", "/usr/share/keyrings"]), "Preparando keyrings apt", dry_run=dry_run)
    _run_compact(sudo_command(["wget", "-q", "-O", "/usr/share/keyrings/postgresql-keyring.asc", "https://www.postgresql.org/media/keys/ACCC4CF8.asc"]), "Descargando llave PostgreSQL PGDG", dry_run=dry_run)

    source_line = f"deb [signed-by=/usr/share/keyrings/postgresql-keyring.asc] https://apt.postgresql.org/pub/repos/apt {codename}-pgdg main\n"
    source_path = "/etc/apt/sources.list.d/postgresql.list"
    if dry_run:
        run_command(["sh", "-c", f"printf %s {source_line!r} > {source_path}"], dry_run=True)
    else:
        tmp_path = Path(tempfile.mkstemp(prefix="postgresql-", suffix=".list")[1])
        tmp_path.write_text(source_line, encoding="utf-8")
        _run_compact(sudo_command(["cp", str(tmp_path), source_path]), "Configurando repo PostgreSQL PGDG")
    _run_compact(sudo_command(["apt", "update", "-y"]), "Actualizando apt con repo PostgreSQL", dry_run=dry_run)


def install_apt_packages(packages: list[str], dry_run: bool = False) -> None:
    if not packages:
        return
    distro = detect_distribution()["id"].lower()
    if distro not in {"ubuntu", "debian", "linuxmint", "pop"}:
        raise RuntimeError(f"Instalación automática de dependencias no soportada para distro: {distro}")
    postgres_version = selected_postgres_version(packages)
    if postgres_version:
        configure_postgresql_apt_repo(postgres_version, dry_run=dry_run)
    _run_compact(sudo_command(["apt", "update", "-y"]), "Actualizando repositorios apt", dry_run=dry_run)
    _run_compact(sudo_command(["apt", "install", "-y", *packages]), f"Instalando: {format_package_list(packages)}", dry_run=dry_run)
