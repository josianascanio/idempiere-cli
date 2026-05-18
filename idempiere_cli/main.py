from __future__ import annotations

import sys

import typer
from rich.console import Console

from idempiere_cli.commands import check, detect, install
from idempiere_cli.interactive import run_main_menu
from idempiere_cli.ui import print_banner

app = typer.Typer(
    name="idempiere-cli",
    help="Developer CLI for installing and managing iDempiere environments.",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    banner: bool = typer.Option(True, "--banner/--no-banner", help="Mostrar banner del CLI."),
) -> None:
    if banner:
        print_banner()
    if ctx.invoked_subcommand is None:
        if sys.stdin.isatty():
            run_main_menu(ctx.get_help())
        else:
            console.print(ctx.get_help())
        raise typer.Exit()


app.command("detect")(detect.detect_command)
app.command("check")(check.check_command)
app.command("install")(install.install_command)


if __name__ == "__main__":
    app()
