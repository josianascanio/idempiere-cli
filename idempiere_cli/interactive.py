from __future__ import annotations

from pathlib import Path

import typer
from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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
    if not str(profile["code"]).isdigit():
        console.print(Panel("El código ambiente debe ser numérico porque se usa para derivar puertos y nombres.", style="red"))
        raise typer.Exit(code=1)
    profile["env"] = inquirer.text(message="Nombre ambiente", default=profile["env"]).execute()
    profile["base_dir"] = inquirer.text(message="Directorio base", default=profile["base_dir"]).execute()
    environment_name = f"{profile['code']}_{profile['env']}"
    profile["idempiere"]["install_path"] = f"{profile['base_dir']}/{environment_name}"
    profile["database"]["name"] = environment_name
    profile["service"]["name"] = environment_name
    profile["ports"]["web"] = int(f"80{profile['code']}")
    profile["ports"]["ssl"] = int(f"84{profile['code']}")
    profile["database"]["host"] = inquirer.text(message="Host PostgreSQL", default=profile["database"]["host"]).execute()
    profile["database"]["port"] = int(inquirer.text(message="Puerto PostgreSQL", default=str(profile["database"]["port"])).execute())
    profile["database"]["user"] = inquirer.text(message="Usuario DB", default=profile["database"]["user"]).execute()
    profile["database"]["password"] = inquirer.secret(message="Password DB", default=profile["database"]["password"]).execute()
    table = Table(title="Valores calculados")
    table.add_column("Campo", style="cyan")
    table.add_column("Valor")
    table.add_row("Ambiente", environment_name)
    table.add_row("Ruta instalación", profile["idempiere"]["install_path"])
    table.add_row("Base de datos", profile["database"]["name"])
    table.add_row("Puerto web", str(profile["ports"]["web"]))
    table.add_row("Puerto SSL", str(profile["ports"]["ssl"]))
    console.print(table)
    deps = detect_dependencies(profile["java"]["required_version"], profile["database"]["version"], False)
    missing = missing_packages(deps)
    selected: list[str] = []
    if missing:
        console.print(Panel("Se detectaron dependencias faltantes requeridas para instalar iDempiere. Si no se instalan, la instalación se detendrá antes de aplicar cambios.", title="Dependencias", style="yellow"))
        for package in missing:
            console.print(f"  - {package}")
        install_missing = inquirer.confirm(message="¿Instalar dependencias faltantes ahora?", default=True).execute()
        selected = missing if install_missing else []
    profile["dependencies"]["install_missing"] = bool(selected)
    return profile, selected


def _ask_profile_path() -> Path:
    return Path(inquirer.text(message="Ruta del perfil YAML", default="profiles/idempiere12-test.example.yml").execute()).expanduser()


def run_main_menu(help_text: str) -> None:
    from idempiere_cli.commands.check import check_command
    from idempiere_cli.commands.detect import detect_command
    from idempiere_cli.commands.install import execute_install

    while True:
        console.print(Panel("Selecciona una acción. Las opciones de detección y validación regresan al menú automáticamente.", title="Menú principal", style="cyan"))
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

        try:
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
        except typer.Exit as exc:
            if exc.exit_code not in (None, 0):
                console.print(Panel("La acción terminó con errores. Revisa los mensajes anteriores.", style="yellow"))
        except Exception as exc:
            console.print(Panel(f"Error: {exc}", style="red"))

        if action in {"Instalar iDempiere interactivo", "Instalar desde perfil YAML"}:
            if not inquirer.confirm(message="¿Volver al menú principal?", default=True).execute():
                return
