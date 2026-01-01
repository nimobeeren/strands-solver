import logging

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

app = typer.Typer()
app.command()(solve)
app.command()(show)
app.command()(benchmark)
app.command()(embed)


def main():
    app()
