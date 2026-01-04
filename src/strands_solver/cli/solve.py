import asyncio
import logging
from enum import Enum
from pathlib import Path
from pprint import pformat
from typing import Annotated

import typer

from ..common import Puzzle, Solution
from ..drawing import draw
from ..nyt import NYT
from ..solver import Solver


class CovererType(str, Enum):
    original = "original"
    cpsat = "cpsat"

logger = logging.getLogger(__name__)


def get_puzzle(puzzle_arg: str) -> Puzzle:
    import datetime
    import json

    if Path(puzzle_arg).exists():
        with Path(puzzle_arg).open("r") as f:
            data = json.load(f)
            return Puzzle(
                name=Path(puzzle_arg).stem,
                theme=data["theme"],
                grid=data["grid"],
                num_words=data["num_words"],
            )
    elif puzzle_arg == "today":
        return NYT().fetch_puzzle(datetime.date.today())
    else:
        try:
            date = datetime.date.fromisoformat(puzzle_arg)
        except ValueError:
            raise ValueError(f"Invalid puzzle argument: {puzzle_arg}")
        return NYT().fetch_puzzle(date)


def write_solutions(solutions: set[Solution], output_dir: Path, puzzle_name: str):
    logging.info("Writing solutions to disk")
    output_dir.mkdir(exist_ok=True)

    for i, solution in enumerate(solutions):
        num_digits = len(str(len(solutions) - 1))
        output_path = output_dir / f"{puzzle_name}.solution.{i:0{num_digits}d}.txt"
        with open(output_path, "w") as f:
            f.write(pformat(solution))

    logging.info(f"All {len(solutions)} solutions written to directory: '{output_dir}'")


async def async_solve(
    puzzle: Puzzle,
    output_dir: Path | None,
    coverer_type: CovererType = CovererType.original,
    timeout: float = 60.0,
    max_solutions: int = 100000,
) -> None:
    logging.info("Solving puzzle:\n")
    print(f"Theme: {puzzle.theme}\n")
    draw(puzzle.grid)
    print(f"\nNumber of words: {puzzle.num_words}")
    print()

    if coverer_type == CovererType.cpsat:
        from ..cpsat_coverer import CPSATGridCoverer

        coverer = CPSATGridCoverer(
            puzzle.grid, timeout_seconds=timeout, max_solutions=max_solutions
        )
        solver = Solver(puzzle, coverer=coverer)
    else:
        solver = Solver(puzzle)

    solutions = await solver.solve()

    if not solutions:
        logging.info("No solutions found")
        return

    best = solutions[0]

    logging.info("Solution:\n")
    draw(puzzle.grid, best)
    print()

    print(f"🟡 {' + '.join(strand.string for strand in best.spangram)} (spangram)")
    for strand in best.non_spangram_strands:
        print(f"🔵 {strand.string}")
    print()

    if output_dir:
        write_solutions(
            solutions=set(solutions), output_dir=output_dir, puzzle_name=puzzle.name
        )


def solve(
    puzzle: Annotated[
        str,
        typer.Argument(
            help="The puzzle to solve. Can be a path to a JSON file, a date in YYYY-MM-DD format, or 'today'"
        ),
    ],
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", "-o", help="Directory to write all solutions to"),
    ] = None,
    coverer: Annotated[
        CovererType,
        typer.Option(
            "--coverer",
            "-c",
            help="Grid covering algorithm: 'original' (backtracking with MRV) or 'cpsat' (OR-Tools CP-SAT solver)",
        ),
    ] = CovererType.original,
    timeout: Annotated[
        float,
        typer.Option(
            "--timeout",
            "-t",
            help="Timeout in seconds for covering (only used with cpsat coverer)",
        ),
    ] = 60.0,
    max_solutions: Annotated[
        int,
        typer.Option(
            "--max-solutions",
            "-m",
            help="Maximum number of covers to find (only used with cpsat coverer)",
        ),
    ] = 100000,
) -> None:
    """Solve a Strands puzzle."""
    try:
        puz = get_puzzle(puzzle)
    except ValueError as e:
        logging.error(str(e))
        raise typer.Exit(1)

    asyncio.run(async_solve(puz, output_dir, coverer, timeout, max_solutions))
