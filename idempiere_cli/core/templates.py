from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


def render_template(template_name: str, context: dict[str, Any]) -> str:
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=False, keep_trailing_newline=True)
    return env.get_template(template_name).render(**context)


def write_template(template_name: str, destination: str | Path, context: dict[str, Any], dry_run: bool = False) -> None:
    output = render_template(template_name, context)
    dest = Path(destination)
    if dry_run:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(output, encoding="utf-8")
