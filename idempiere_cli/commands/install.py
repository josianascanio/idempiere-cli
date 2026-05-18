from __future__ import annotations

import shutil
import tempfile
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from idempiere_cli.commands.check import collect_checks, print_checks
from idempiere_cli.core.config import derive_profile_values, load_profile
from idempiere_cli.core.dependencies import detect_dependencies, install_apt_packages, missing_packages
from idempiere_cli.core.detection import detect_installer
from idempiere_cli.core.postgres import database_exists
from idempiere_cli.core.shell import run_command, sudo_command
from idempiere_cli.core.templates import render_template, write_template
from idempiere_cli.interactive import build_interactive_profile

console = Console()


def resolve_installer(profile: dict, explicit_installer: str | None = None, auto_detect: bool = False) -> str:
    if explicit_installer:
        return explicit_installer
    configured = profile.get("installer", "auto")
    if configured != "auto" and not auto_detect:
        return configured
    installer, reason = detect_installer()
    if not installer:
        raise typer.BadParameter(f"No se pudo detectar instalador automáticamente: {reason}")
    return installer


def print_install_summary(profile: dict, installer: str, dry_run: bool, packages: list[str]) -> None:
    table = Table(title="Resumen de instalación")
    table.add_column("Campo", style="cyan")
    table.add_column("Valor")
    table.add_row("Modo", "DRY-RUN" if dry_run else "REAL")
    table.add_row("Versión", str(profile["version"]))
    table.add_row("Instalador", installer)
    table.add_row("Ambiente", f"{profile['code']}_{profile['env']}")
    table.add_row("Ruta", profile["idempiere"]["install_path"])
    table.add_row("Download", profile["idempiere"]["download_url"])
    table.add_row("Base de datos", f"{profile['database']['name']} en {profile['database']['host']}:{profile['database']['port']}")
    table.add_row("Puertos", f"web={profile['ports']['web']} ssl={profile['ports']['ssl']} shutdown={profile['ports']['shutdown']}")
    table.add_row("Servicio", profile.get("service", {}).get("name", f"{profile['code']}_{profile['env']}"))
    table.add_row("Dependencias faltantes a instalar", ", ".join(packages) if packages else "ninguna")
    console.print(table)


def planned_actions(profile: dict, packages: list[str]) -> list[str]:
    install_path = profile["idempiere"]["install_path"]
    actions = []
    if packages:
        actions.append(f"Instalar dependencias con apt: {', '.join(packages)}")
    actions.extend(
        [
            f"Crear directorio {install_path}",
            "Descargar ZIP de iDempiere",
            "Extraer ZIP",
            f"Copiar idempiere-server a {install_path}",
            "Generar idempiereEnv.properties",
            "Ejecutar silent-setup-alt.sh",
        ]
    )
    if profile.get("install", {}).get("create_database", True):
        actions.append("Ejecutar utils/RUN_ImportIdempiere.sh")
    actions.extend(["Ejecutar utils/RUN_SyncDB.sh", "Ejecutar sign-database-build-alt.sh"])
    if profile.get("install", {}).get("create_service", True):
        actions.append("Crear servicio systemd")
    return actions


def print_plan(profile: dict, packages: list[str]) -> None:
    table = Table(title="Plan de ejecución")
    table.add_column("#", justify="right")
    table.add_column("Acción")
    for index, action in enumerate(planned_actions(profile, packages), start=1):
        table.add_row(str(index), action)
    console.print(table)


def _download_and_extract(profile: dict, dry_run: bool) -> Path:
    tmp_dir = Path(tempfile.mkdtemp(prefix="idempiere-cli-"))
    zip_path = tmp_dir / "idempiere.zip"
    run_command(["wget", "--progress=bar:force:noscroll", "-O", str(zip_path), profile["idempiere"]["download_url"]], dry_run=dry_run)
    run_command(["unzip", "-o", str(zip_path), "-d", str(tmp_dir)], dry_run=dry_run)
    return tmp_dir


def _find_extracted_server(tmp_dir: Path) -> Path:
    candidates = list(tmp_dir.glob("**/idempiere-server"))
    if not candidates:
        raise RuntimeError("No se encontró idempiere-server dentro del ZIP extraído")
    return candidates[0]


def _copy_installation(source: Path, destination: Path, dry_run: bool, force: bool) -> None:
    if dry_run:
        console.print(f"[yellow]DRY-RUN:[/yellow] copiar {source} -> {destination}")
        return
    if destination.exists() and any(destination.iterdir()):
        if not force:
            raise RuntimeError(f"La ruta destino no está vacía: {destination}. Usa --force para sobrescribir.")
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def _write_env(profile: dict, dry_run: bool) -> None:
    destination = Path(profile["idempiere"]["install_path"]) / "idempiereEnv.properties"
    if dry_run:
        console.print(f"[yellow]DRY-RUN:[/yellow] generar {destination}")
        console.print(render_template("idempiereEnv.properties.j2", {"profile": profile})[:1200])
        return
    write_template("idempiereEnv.properties.j2", destination, {"profile": profile})


def _run_idempiere_setup(profile: dict, dry_run: bool) -> None:
    home = Path(profile["idempiere"]["install_path"])
    run_command(["sh", "silent-setup-alt.sh"], cwd=home, dry_run=dry_run)
    if profile.get("install", {}).get("create_database", True):
        run_command(["bash", "utils/RUN_ImportIdempiere.sh"], cwd=home, dry_run=dry_run)
    run_command(["sh", "RUN_SyncDB.sh"], cwd=home / "utils", dry_run=dry_run)
    run_command(["sh", "sign-database-build-alt.sh"], cwd=home, dry_run=dry_run)


def _create_systemd_service(profile: dict, dry_run: bool) -> None:
    service = profile.get("service", {})
    if not profile.get("install", {}).get("create_service", True):
        return
    name = service.get("name", f"{profile['code']}_{profile['env']}")
    destination = Path("/etc/systemd/system") / f"{name}.service"
    content = render_template("systemd.service.j2", {"profile": profile})
    if dry_run:
        console.print(f"[yellow]DRY-RUN:[/yellow] generar {destination}")
        console.print(content)
        run_command(sudo_command(["systemctl", "daemon-reload"]), dry_run=True)
        run_command(sudo_command(["systemctl", "enable", name]), dry_run=True)
        return
    tmp_file = Path(tempfile.mkstemp(prefix=f"{name}-", suffix=".service")[1])
    tmp_file.write_text(content, encoding="utf-8")
    run_command(sudo_command(["cp", str(tmp_file), str(destination)]))
    run_command(sudo_command(["systemctl", "daemon-reload"]))
    run_command(sudo_command(["systemctl", "enable", name]))


def perform_install(profile: dict, packages: list[str], dry_run: bool, force: bool) -> None:
    install_path = Path(profile["idempiere"]["install_path"])
    if database_exists(profile["database"]["name"], profile["database"].get("admin_user", "postgres"), dry_run=dry_run) and not force:
        raise RuntimeError(f"La base {profile['database']['name']} ya existe. Usa --force si estás seguro.")
    install_apt_packages(packages, dry_run=dry_run)
    if dry_run:
        run_command(sudo_command(["mkdir", "-p", str(install_path)]), dry_run=True)
        _download_and_extract(profile, dry_run=True)
        _write_env(profile, dry_run=True)
        _run_idempiere_setup(profile, dry_run=True)
        _create_systemd_service(profile, dry_run=True)
        return
    run_command(sudo_command(["mkdir", "-p", str(install_path)]))
    tmp_dir = _download_and_extract(profile, dry_run=False)
    server_dir = _find_extracted_server(tmp_dir)
    _copy_installation(server_dir, install_path, dry_run=False, force=force)
    _write_env(profile, dry_run=False)
    _run_idempiere_setup(profile, dry_run=False)
    _create_systemd_service(profile, dry_run=False)


def install_command(
    profile: Path | None = typer.Option(None, "--profile", "-p", help="Perfil YAML."),
    interactive: bool = typer.Option(False, "--interactive", help="Construir perfil interactivo."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Mostrar acciones sin aplicar cambios."),
    force: bool = typer.Option(False, "--force", help="Permitir sobrescrituras controladas."),
    installer: str | None = typer.Option(None, "--installer", help="Forzar instalador: 12-x86, 12-arm o 12-debian."),
    auto_detect: bool = typer.Option(False, "--auto-detect", help="Forzar detección automática de instalador."),
    install_dependencies: bool | None = typer.Option(None, "--install-dependencies/--no-install-dependencies", help="Instalar dependencias faltantes."),
) -> None:
    if interactive:
        data, selected_packages = build_interactive_profile()
    elif profile:
        data = load_profile(profile)
        selected_packages = []
    else:
        raise typer.BadParameter("Usa --profile o --interactive")
    data = derive_profile_values(data)
    selected_installer = resolve_installer(data, installer, auto_detect)
    deps = detect_dependencies(data["java"].get("required_version", 17), data["database"].get("version", 15), data.get("nginx", {}).get("enabled", False))
    missing = missing_packages(deps)
    should_install_deps = data.get("dependencies", {}).get("install_missing", False)
    if install_dependencies is not None:
        should_install_deps = install_dependencies
    packages = selected_packages or (missing if should_install_deps else [])

    checks = collect_checks(data, selected_installer)
    print_checks(checks)
    def is_resolved_by_dependency_install(name: str) -> bool:
        if not packages:
            return False
        return name.startswith("Comando") or name in {"Java", "PostgreSQL"}

    blocking_errors = [result for result in checks if result.status == "ERROR" and not is_resolved_by_dependency_install(result.name)]
    if blocking_errors:
        raise typer.Exit(code=1)

    print_install_summary(data, selected_installer, dry_run, packages)
    print_plan(data, packages)
    if dry_run:
        console.print(Panel("DRY-RUN activo: no se aplicarán cambios en el servidor.", style="yellow"))
        perform_install(data, packages, dry_run=True, force=force)
        return
    if os.geteuid() != 0:
        console.print("[red]ERROR:[/red] La instalación real debe ejecutarse como root. Usa `sudo idempiere-cli install ...`.")
        raise typer.Exit(code=1)
    if not force and not Confirm.ask("¿Aplicar esta instalación real?", default=False):
        console.print("Instalación cancelada.")
        raise typer.Exit()
    perform_install(data, packages, dry_run=False, force=force)
    console.print(Panel("Instalación finalizada.", style="green"))
