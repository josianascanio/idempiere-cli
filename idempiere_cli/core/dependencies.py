from __future__ import annotations

from dataclasses import dataclass

from idempiere_cli.core.detection import detect_distribution
from idempiere_cli.core.shell import command_exists, run_command, sudo_command


BASE_PACKAGES = ["curl", "wget", "unzip", "tar", "fontconfig", "git"]


@dataclass
class Dependency:
    name: str
    command: str
    package: str
    installed: bool
    required: bool = True


def detect_dependencies(java_version: int = 17, postgres_version: int = 15, include_nginx: bool = False) -> list[Dependency]:
    deps = [Dependency(pkg, pkg, pkg, command_exists(pkg)) for pkg in BASE_PACKAGES]
    deps.extend(
        [
            Dependency(f"Java {java_version}", "java", f"openjdk-{java_version}-jdk-headless", command_exists("java")),
            Dependency(f"PostgreSQL {postgres_version}", "psql", f"postgresql-{postgres_version}", command_exists("psql")),
            Dependency("psql", "psql", "postgresql-client", command_exists("psql")),
            Dependency("pg_dump", "pg_dump", "postgresql-client", command_exists("pg_dump")),
            Dependency("pg_restore", "pg_restore", "postgresql-client", command_exists("pg_restore")),
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


def install_apt_packages(packages: list[str], dry_run: bool = False) -> None:
    if not packages:
        return
    distro = detect_distribution()["id"].lower()
    if distro not in {"ubuntu", "debian", "linuxmint", "pop"}:
        raise RuntimeError(f"Instalación automática de dependencias no soportada para distro: {distro}")
    run_command(sudo_command(["apt", "update", "-y"]), dry_run=dry_run)
    run_command(sudo_command(["apt", "install", "-y", *packages]), dry_run=dry_run)
