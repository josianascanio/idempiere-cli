from __future__ import annotations

from pathlib import Path

import typer
from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel

from idempiere_cli.core.config import default_profile
from idempiere_cli.core.dependencies import detect_dependencies, missing_packages
from idempiere_cli.core.detection import detect_installer

console = Console()


def build_interactive_profile() -> tuple[dict, list[str]]:
    version = int(
        inquirer.select(
            message="Versión de iDempiere",
            choices=["12"],
            default="12",
        ).execute()
    )
    profile = default_profile(version)
    installer, _ = detect_installer()
    if not installer:
        console.print(Panel("No hay instalador compatible para este sistema. Por ahora el CLI soporta iDempiere 12 en 12-x86, 12-arm o 12-debian.", style="red"))
        raise typer.Exit(code=1)
    profile["installer"] = inquirer.select(
        message="Instalador",
        choices=["auto", "12-x86", "12-arm", "12-debian"],
        default=installer or "auto",
    ).execute()
    profile["code"] = inquirer.text(message="Código ambiente", default=profile["code"]).execute()
    profile["env"] = inquirer.text(message="Nombre ambiente", default=profile["env"]).execute()
    profile["base_dir"] = inquirer.text(message="Directorio base", default=profile["base_dir"]).execute()
    install_path = f"{profile['base_dir']}/{profile['code']}_{profile['env']}"
    profile["idempiere"]["install_path"] = inquirer.text(message="Ruta instalación", default=install_path).execute()
    profile["database"]["name"] = inquirer.text(message="Nombre base de datos", default=f"{profile['code']}_{profile['env']}").execute()
    profile["database"]["host"] = inquirer.text(message="Host PostgreSQL", default=profile["database"]["host"]).execute()
    profile["database"]["port"] = int(inquirer.text(message="Puerto PostgreSQL", default=str(profile["database"]["port"])).execute())
    profile["database"]["user"] = inquirer.text(message="Usuario DB", default=profile["database"]["user"]).execute()
    profile["database"]["password"] = inquirer.secret(message="Password DB", default=profile["database"]["password"]).execute()
    profile["ports"]["web"] = int(inquirer.text(message="Puerto web", default=str(profile["ports"]["web"])).execute())
    profile["ports"]["ssl"] = int(inquirer.text(message="Puerto SSL", default=str(profile["ports"]["ssl"])).execute())
    profile["ports"]["shutdown"] = int(inquirer.text(message="Puerto shutdown", default=str(profile["ports"]["shutdown"])).execute())
    deps = detect_dependencies(profile["java"]["required_version"], profile["database"]["version"], False)
    missing = missing_packages(deps)
    selected: list[str] = []
    if missing:
        selected = inquirer.checkbox(
            message="Dependencias faltantes a instalar",
            choices=missing,
            default=missing,
        ).execute()
    profile["dependencies"]["install_missing"] = bool(selected)
    return profile, selected


def _ask_profile_path() -> Path:
    return Path(inquirer.text(message="Ruta del perfil YAML", default="profiles/idempiere12-test.example.yml").execute()).expanduser()


def run_main_menu(help_text: str) -> None:
    from idempiere_cli.commands.check import check_command
    from idempiere_cli.commands.detect import detect_command
    from idempiere_cli.commands.install import execute_install

    while True:
        action = inquirer.select(
            message="¿Qué quieres hacer?",
            choices=[
                "Detectar infraestructura",
                "Validar servidor",
                "Instalar iDempiere interactivo",
                "Simular instalación interactiva (--dry-run)",
                "Instalar desde perfil YAML",
                "Simular desde perfil YAML (--dry-run)",
                "Ver ayuda",
                "Salir",
            ],
        ).execute()

        if action == "Detectar infraestructura":
            detect_command()
        elif action == "Validar servidor":
            check_command(profile=None, target_version=12, installer=None)
        elif action == "Instalar iDempiere interactivo":
            execute_install(interactive=True, dry_run=False)
        elif action == "Simular instalación interactiva (--dry-run)":
            execute_install(interactive=True, dry_run=True)
        elif action == "Instalar desde perfil YAML":
            execute_install(profile=_ask_profile_path(), dry_run=False)
        elif action == "Simular desde perfil YAML (--dry-run)":
            execute_install(profile=_ask_profile_path(), dry_run=True)
        elif action == "Ver ayuda":
            console.print(help_text)
        elif action == "Salir":
            console.print("Saliendo de idempiere-cli.")
            return

        if action != "Salir" and not inquirer.confirm(message="¿Volver al menú principal?", default=True).execute():
            return
