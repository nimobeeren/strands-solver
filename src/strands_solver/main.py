import argparse
import datetime
import json
import logging
from pathlib import Path
from pprint import pformat

from .common import Puzzle, Solution
from .drawing import draw
from .grid_coverer import GridCoverer
from .puzzle_fetcher import PuzzleFetcher
from .solution_ranker import SolutionRanker
from .solver import Solver
from .spangram_finder import SpangramFinder
from .word_finder import WordFinder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_puzzle(puzzle_arg: str) -> Puzzle:
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
        return PuzzleFetcher().fetch_puzzle(datetime.date.today())
    else:
        try:
            date = datetime.date.fromisoformat(puzzle_arg)
        except ValueError:
            raise ValueError(f"Invalid puzzle argument: {puzzle_arg}")
        return PuzzleFetcher().fetch_puzzle(date)


def write_solutions(solutions: set[Solution], output_dir: Path, puzzle_name: str):
    logging.info("Writing solutions to disk")
    output_dir.mkdir(exist_ok=True)

    # Write each solution to its own file in output directory
    for i, solution in enumerate(solutions):
        num_digits = len(str(len(solutions) - 1))
        output_path = output_dir / f"{puzzle_name}.solution.{i:0{num_digits}d}.txt"
        with open(output_path, "w") as f:
            f.write(pformat(solution))

    logging.info(f"All {len(solutions)} solutions written to directory: '{output_dir}'")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "puzzle",
        type=str,
        help="The puzzle to solve. Can be a path to a JSON file containing a puzzle, a date in YYYY-MM-DD format, or 'today'",
    )
    parser.add_argument(
        "-o", "--output-dir", type=Path, help="Directory to write all solutions to"
    )
    args = parser.parse_args()

    try:
        puzzle = get_puzzle(args.puzzle)
    except ValueError as e:
        logging.error(str(e))
        parser.print_help()
        return 1

    logging.info("Solving puzzle:\n")
    print(f"Theme: {puzzle.theme}\n")
    draw(puzzle.grid)
    print(f"\nNumber of words: {puzzle.num_words}")
    print()

    finder = WordFinder(puzzle.grid)
    coverer = GridCoverer(puzzle.grid)
    spangram_finder = SpangramFinder(puzzle.grid, num_words=puzzle.num_words)
    solver = Solver(finder=finder, coverer=coverer, spangram_finder=spangram_finder)
    solutions = solver.solve()

    ranker = SolutionRanker()
    solution = ranker.find_best(solutions)

    if solution is None:
        logging.info("No solutions found")
        return

    logging.info("Best solution:\n")
    draw(puzzle.grid, solution)
    print()

    print(f"🟡 {' + '.join(strand.string for strand in solution.spangram)} (spangram)")
    for strand in solution.non_spangram_strands:
        print(f"🔵 {strand.string}")
    print()

    output_dir: Path | None = args.output_dir
    if output_dir:
        write_solutions(
            solutions=solutions, output_dir=output_dir, puzzle_name=puzzle.name
        )


if __name__ == "__main__":
    raise SystemExit(main())
