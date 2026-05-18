from __future__ import annotations

from InquirerPy import inquirer

from idempiere_cli.core.config import default_profile
from idempiere_cli.core.dependencies import detect_dependencies, missing_packages
from idempiere_cli.core.detection import detect_installer


def build_interactive_profile() -> tuple[dict, list[str]]:
    version = int(inquirer.select(message="Versión de iDempiere", choices=["12", "11", "10"], default="12").execute())
    profile = default_profile(version)
    installer, _ = detect_installer()
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
