import datetime
from typing import Annotated

import typer

from ..drawing import draw
from ..nyt import NYT


def get_date(date_arg: str) -> datetime.date:
    if date_arg == "today":
        return datetime.date.today()
    try:
        return datetime.date.fromisoformat(date_arg)
    except ValueError:
        raise ValueError(f"Invalid date argument: {date_arg}")


def show(
    date: Annotated[
        str,
        typer.Argument(
            help="The date of the puzzle. Can be 'today' or a date in YYYY-MM-DD format."
        ),
    ],
) -> None:
    """Display the official solution for a Strands puzzle."""
    try:
        parsed_date = get_date(date)
    except ValueError as e:
        print(f"Error: {e}")
        raise typer.Exit(1)

    nyt = NYT()
    puzzle = nyt.fetch_puzzle(parsed_date)
    solution = nyt.fetch_solution(parsed_date)

    print(f"Theme: {puzzle.theme}\n")
    draw(puzzle.grid, solution)
    print()

    print(f"🟡 {solution.spangram[0].string} (spangram)")
    for strand in sorted(solution.non_spangram_strands, key=lambda s: s.string):
        print(f"🔵 {strand.string}")
