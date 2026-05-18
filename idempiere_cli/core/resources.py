from __future__ import annotations

import shutil
from dataclasses import dataclass


@dataclass
class ValidationResult:
    name: str
    status: str
    message: str


def _meminfo_value_kb(key: str) -> int:
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith(key):
                    return int(line.split()[1])
    except FileNotFoundError:
        return 0
    return 0


def get_total_ram_gb() -> float:
    return round(_meminfo_value_kb("MemTotal:") / 1024 / 1024, 2)


def get_available_ram_gb() -> float:
    value = _meminfo_value_kb("MemAvailable:") or _meminfo_value_kb("MemFree:")
    return round(value / 1024 / 1024, 2)


def get_disk_free_gb(path: str) -> float:
    usage = shutil.disk_usage(path)
    return round(usage.free / 1024 / 1024 / 1024, 2)


def validate_ram(min_gb: float, recommended_gb: float) -> ValidationResult:
    total = get_total_ram_gb()
    if total <= 0:
        return ValidationResult("RAM", "WARNING", "No se pudo leer /proc/meminfo")
    if total < min_gb:
        return ValidationResult("RAM", "ERROR", f"{total} GB disponibles, mínimo {min_gb} GB")
    if total < recommended_gb:
        return ValidationResult("RAM", "WARNING", f"{total} GB, recomendado {recommended_gb} GB")
    return ValidationResult("RAM", "OK", f"{total} GB")


def validate_disk(path: str, min_gb: float, recommended_gb: float) -> ValidationResult:
    try:
        free = get_disk_free_gb(path)
    except FileNotFoundError:
        return ValidationResult("Disco", "ERROR", f"Ruta no existe: {path}")
    if free < min_gb:
        return ValidationResult("Disco", "ERROR", f"{free} GB libres en {path}, mínimo {min_gb} GB")
    if free < recommended_gb:
        return ValidationResult("Disco", "WARNING", f"{free} GB libres en {path}, recomendado {recommended_gb} GB")
    return ValidationResult("Disco", "OK", f"{free} GB libres en {path}")
