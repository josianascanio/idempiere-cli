from __future__ import annotations

import typer
from rich.console import Console

from idempiere_cli.commands import check, detect, install
from idempiere_cli.ui import print_banner

app = typer.Typer(
    name="idempiere-cli",
    help="Developer CLI for installing and managing iDempiere environments.",
    no_args_is_help=True,
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
        console.print(ctx.get_help())
        raise typer.Exit()


app.command("detect")(detect.detect_command)
app.command("check")(check.check_command)
app.command("install")(install.install_command)


if __name__ == "__main__":
    app()
