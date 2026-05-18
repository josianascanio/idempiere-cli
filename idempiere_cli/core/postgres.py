from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from idempiere_cli.core.resources import ValidationResult
from idempiere_cli.core.shell import command_exists, run_command, sudo_command


def is_postgres_installed() -> bool:
    return command_exists("psql") or command_exists("pg_lsclusters")


def get_pg_clusters() -> list[dict[str, str]]:
    if not command_exists("pg_lsclusters"):
        return []
    result = subprocess.run(["pg_lsclusters", "--no-header"], text=True, capture_output=True)
    clusters: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4:
            clusters.append({"version": parts[0], "cluster": parts[1], "port": parts[2], "status": parts[3]})
    return clusters


def get_pg_versions() -> list[str]:
    versions = {cluster["version"] for cluster in get_pg_clusters()}
    if command_exists("psql"):
        result = subprocess.run(["psql", "--version"], text=True, capture_output=True)
        match = re.search(r"(\d+(?:\.\d+)?)", result.stdout)
        if match:
            versions.add(match.group(1))
    return sorted(versions)


def validate_postgres(min_version: int = 13) -> ValidationResult:
    if not is_postgres_installed():
        return ValidationResult("PostgreSQL", "ERROR", "No detectado")
    versions = get_pg_versions()
    if not versions:
        return ValidationResult("PostgreSQL", "WARNING", "Detectado, pero sin versión")
    majors = [int(version.split(".")[0]) for version in versions if version.split(".")[0].isdigit()]
    if majors and max(majors) < min_version:
        return ValidationResult("PostgreSQL", "WARNING", f"Versiones {', '.join(versions)}, recomendado {min_version}+")
    clusters = get_pg_clusters()
    suffix = f"; clusters: {len(clusters)}" if clusters else ""
    return ValidationResult("PostgreSQL", "OK", f"Versiones {', '.join(versions)}{suffix}")


def check_pg_port(port: int) -> bool:
    return any(str(port) == cluster.get("port") for cluster in get_pg_clusters())


def database_exists(name: str, admin_user: str = "postgres", dry_run: bool = False) -> bool:
    if dry_run:
        return False
    if not command_exists("psql"):
        return False
    result = subprocess.run(
        ["psql", "-U", admin_user, "-tAc", f"SELECT 1 FROM pg_database WHERE datname='{name}'"],
        text=True,
        capture_output=True,
    )
    return result.stdout.strip() == "1"


def create_database(name: str, owner: str, admin_user: str = "postgres", dry_run: bool = False) -> None:
    command = sudo_command(["createdb", "-U", admin_user, "-O", owner, name])
    run_command(command, dry_run=dry_run)


def configure_local_postgres(version: int, dry_run: bool = False) -> None:
    config_dir = Path(f"/etc/postgresql/{version}/main")
    pg_hba = config_dir / "pg_hba.conf"
    if dry_run:
        run_command(sudo_command(["test", "-d", str(config_dir)]), dry_run=True)
    elif not config_dir.exists():
        return

    content = """local   all             postgres                                peer
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
"""
    if dry_run:
        run_command(["sh", "-c", f"printf %s {content!r} > {pg_hba}"], dry_run=True)
    else:
        tmp_path = Path(tempfile.mkstemp(prefix="pg_hba-", suffix=".conf")[1])
        tmp_path.write_text(content, encoding="utf-8")
        run_command(sudo_command(["cp", str(tmp_path), str(pg_hba)]), stream=True)

    if command_exists("sudo"):
        password_command = ["sudo", "-u", "postgres", "psql", "-U", "postgres", "-c", "alter user postgres password 'postgres';"]
    else:
        password_command = ["runuser", "-u", "postgres", "--", "psql", "-U", "postgres", "-c", "alter user postgres password 'postgres';"]
    run_command(password_command, dry_run=dry_run, check=False, stream=not dry_run)
    run_command(sudo_command(["systemctl", "enable", "postgresql"]), dry_run=dry_run, check=False, stream=not dry_run)
    run_command(sudo_command(["systemctl", "restart", "postgresql"]), dry_run=dry_run, check=False, stream=not dry_run)
