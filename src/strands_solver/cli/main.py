import logging
from importlib.metadata import version

import typer
from dotenv import load_dotenv

from .benchmark import benchmark
from .embed import embed
from .show import show
from .solve import solve

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def version_callback(value: bool) -> None:
    if value:
        print(f"strands-solver {version('strands-solver')}")
        raise typer.Exit()


app = typer.Typer()


@app.callback(invoke_without_command=True)
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    pass


app.command()(solve)
app.command()(show)
app.command()(benchmark)
app.command()(embed)


def main():
    app()


if __name__ == "__main__":
    main()
