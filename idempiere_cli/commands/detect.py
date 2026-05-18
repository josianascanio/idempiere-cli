from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from idempiere_cli.core.detection import detect_environment_summary
from idempiere_cli.core.java import get_installed_javas, get_java_version
from idempiere_cli.core.ports import get_listening_ports
from idempiere_cli.core.postgres import get_pg_clusters, get_pg_versions, is_postgres_installed
from idempiere_cli.core.shell import command_exists

console = Console()


def detect_command() -> None:
    summary = detect_environment_summary()
    table = Table(title="Infraestructura detectada")
    table.add_column("Elemento", style="cyan")
    table.add_column("Valor", style="white")
    table.add_row("OS", str(summary["os"]))
    table.add_row("Distribución", f"{summary['distribution']} ({summary['distribution_version']})")
    table.add_row("Arquitectura", str(summary["architecture"]))
    table.add_row("Kernel", str(summary["kernel"]))
    table.add_row("CPU", str(summary["cpu"]))
    table.add_row("RAM total", f"{summary['ram_total_gb']} GB")
    table.add_row("RAM disponible", f"{summary['ram_available_gb']} GB")
    table.add_row("Disco /opt", f"{summary['disk_free_gb']} GB" if summary["disk_free_gb"] is not None else "No existe /opt")
    table.add_row("PostgreSQL", "instalado" if is_postgres_installed() else "no detectado")
    versions = get_pg_versions()
    table.add_row("Versiones PostgreSQL", ", ".join(versions) if versions else "no detectadas")
    clusters = get_pg_clusters()
    cluster_text = ", ".join(f"{c['version']}/{c['cluster']} en {c['port']} ({c['status']})" for c in clusters)
    table.add_row("Clústeres PostgreSQL", cluster_text or "no detectados")
    table.add_row("Java", get_java_version() or "no detectado")
    javas = get_installed_javas()
    table.add_row("JAVA_HOME candidatos", "\n".join(javas) if javas else "no detectados")
    table.add_row("Nginx", "instalado" if command_exists("nginx") else "no detectado")
    relevant_ports = [line for line in get_listening_ports() if any(f":{port}" in line for port in [8080, 8480, 5432, 5433])]
    table.add_row("Puertos relevantes", "\n".join(relevant_ports[:8]) if relevant_ports else "sin puertos relevantes detectados")
    table.add_row("Instalador recomendado", str(summary["recommended_installer"] or "WARNING: selección manual requerida"))
    table.add_row("Razón", str(summary["installer_reason"]))
    console.print(table)
    console.print(Panel("Usa `idempiere-cli check` para validar si el servidor está listo.", style="green"))
