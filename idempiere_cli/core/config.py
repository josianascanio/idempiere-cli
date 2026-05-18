from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

VALID_INSTALLERS = {"auto", "12-x86", "12-arm", "12-debian"}


def load_profile(path: str | Path) -> dict[str, Any]:
    profile_path = Path(path).expanduser()
    if not profile_path.exists():
        raise FileNotFoundError(f"Perfil no existe: {profile_path}")
    with profile_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    validate_profile(data)
    return data


def validate_profile(profile: dict[str, Any]) -> None:
    required = ["version", "code", "env", "base_dir", "database", "java", "ports", "resources", "idempiere"]
    missing = [key for key in required if key not in profile]
    if missing:
        raise ValueError(f"Perfil incompleto. Faltan campos: {', '.join(missing)}")
    installer = profile.get("installer", "auto")
    if installer not in VALID_INSTALLERS:
        raise ValueError(f"installer inválido: {installer}. Valores: {', '.join(sorted(VALID_INSTALLERS))}")


def default_profile(version: int = 12) -> dict[str, Any]:
    required_java = 17 if version >= 12 else 11
    return {
        "version": version,
        "installer": "auto",
        "code": "80",
        "env": "idempiere",
        "base_dir": "/opt/sas",
        "java": {"home": f"/usr/lib/jvm/java-{required_java}-openjdk-amd64", "required_version": required_java},
        "database": {
            "engine": "postgresql",
            "version": 15,
            "host": "localhost",
            "port": 5432,
            "name": "80_idempiere",
            "user": "adempiere",
            "password": "adempiere",
            "admin_user": "postgres",
        },
        "resources": {"min_ram_gb": 4, "recommended_ram_gb": 8, "min_disk_gb": 20, "recommended_disk_gb": 50, "disk_check_path": "/opt"},
        "ports": {"web": 8080, "ssl": 8480},
        "service": {"name": "80_idempiere", "user": "idempiere", "type": "systemd"},
        "nginx": {"enabled": False, "domain": "test.example.com", "ssl_enabled": False},
        "idempiere": {
            "download_url": "https://sourceforge.net/projects/idempiere/files/v12/daily-server/idempiereServer12Daily.gtk.linux.x86_64.zip/download",
            "install_path": "/opt/sas/80_idempiere",
        },
        "install": {"create_database": True, "restore_database": False, "create_service": True, "configure_nginx": False},
        "dependencies": {"install_missing": False, "base": True, "java": True, "postgres": True, "nginx": False, "packages": ["curl", "wget", "unzip", "tar", "fontconfig", "git"]},
    }


def derive_profile_values(profile: dict[str, Any]) -> dict[str, Any]:
    code = str(profile["code"])
    env = str(profile["env"])
    base_dir = profile["base_dir"]
    install_path = profile.get("idempiere", {}).get("install_path") or f"{base_dir}/{code}_{env}"
    profile.setdefault("idempiere", {})["install_path"] = install_path
    profile.setdefault("database", {}).setdefault("name", f"{code}_{env}")
    profile.setdefault("service", {}).setdefault("name", f"{code}_{env}")
    profile.setdefault("ports", {}).setdefault("web", int(f"80{code}"))
    profile.setdefault("ports", {}).setdefault("ssl", int(f"84{code}"))
    return profile
