from __future__ import annotations

import tempfile
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from idempiere_cli.core.dependencies import install_apt_packages
from idempiere_cli.core.shell import run_command, sudo_command
from idempiere_cli.core.templates import render_template

console = Console()


def install_nginx(dry_run: bool = False) -> None:
    install_apt_packages(["nginx"], dry_run=dry_run)


def create_site(
    domain: str,
    backend_port: int = 8080,
    dry_run: bool = False,
    force: bool = False,
    ssl_enabled: bool = False,
    ssl_certificate: str = "",
    ssl_certificate_key: str = "",
) -> None:
    profile = {
        "nginx": {
            "domain": domain,
            "ssl_enabled": ssl_enabled,
            "ssl_certificate": ssl_certificate,
            "ssl_certificate_key": ssl_certificate_key,
        },
        "ports": {"web": backend_port},
    }
    content = render_template("nginx.conf.j2", {"profile": profile})
    available = Path("/etc/nginx/sites-available") / domain
    enabled = Path("/etc/nginx/sites-enabled") / domain

    if dry_run:
        console.print(f"[yellow]DRY-RUN:[/yellow] generar {available}")
        console.print(content)
        run_command(sudo_command(["ln", "-sf", str(available), str(enabled)]), dry_run=True)
        run_command(sudo_command(["nginx", "-t"]), dry_run=True)
        run_command(sudo_command(["systemctl", "reload", "nginx"]), dry_run=True)
        return

    if available.exists() and not force:
        raise RuntimeError(f"El site ya existe: {available}. Usa force si quieres sobrescribirlo.")
    tmp_path = Path(tempfile.mkstemp(prefix=f"nginx-{domain}-", suffix=".conf")[1])
    tmp_path.write_text(content, encoding="utf-8")
    run_command(sudo_command(["mkdir", "-p", "/etc/nginx/sites-available", "/etc/nginx/sites-enabled"]), stream=True)
    run_command(sudo_command(["cp", str(tmp_path), str(available)]), stream=True)
    run_command(sudo_command(["ln", "-sf", str(available), str(enabled)]), stream=True)
    test_nginx()
    reload_nginx()
    console.print(Panel(f"Site Nginx creado: {domain} -> http://127.0.0.1:{backend_port}", style="green"))


def test_nginx(dry_run: bool = False) -> None:
    run_command(sudo_command(["nginx", "-t"]), dry_run=dry_run, stream=not dry_run)


def reload_nginx(dry_run: bool = False) -> None:
    run_command(sudo_command(["systemctl", "reload", "nginx"]), dry_run=dry_run, stream=not dry_run)
