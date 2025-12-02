import argparse
import json
import logging
from pathlib import Path
from pprint import pformat

from .coverer import Coverer
from .draw import draw
from .finder import Finder
from .ranker import Ranker
from .solver import Solver
from .spangram_finder import SpangramFinder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "puzzle", type=str, help="Path to a JSON file containing a puzzle"
    )
    parser.add_argument(
        "-o", "--output-dir", type=Path, help="Directory to write all solutions to"
    )
    args = parser.parse_args()

    with open(args.puzzle, "r") as f:
        puzzle = json.load(f)
        theme = puzzle["theme"]
        grid = puzzle["grid"]
        num_words = puzzle["num_words"]

    logging.info("Solving puzzle:\n")
    print(f"Theme: {theme}\n")
    draw(grid)
    print(f"\nNumber of words: {num_words}")
    print()

    finder = Finder(grid)
    coverer = Coverer(grid)
    spangram_finder = SpangramFinder(grid, num_words=num_words)
    solver = Solver(finder=finder, coverer=coverer, spangram_finder=spangram_finder)
    solutions = solver.solve()

    ranker = Ranker()
    solution = ranker.find_best(solutions)

    if solution is None:
        logging.info("No solutions found")
        return

    logging.info("Best solution:\n")
    draw(grid, solution)
    print()

    print(f"🟡 {' + '.join(strand.string for strand in solution.spangram)} (spangram)")
    for strand in solution.non_spangram_strands:
        print(f"🔵 {strand.string}")
    print()

    output_dir: Path | None = args.output_dir
    if output_dir:
        logging.info("Writing solutions to disk")
        output_dir.mkdir(exist_ok=True)
        puzzle_name = Path(args.puzzle).stem

        # Write each solution to its own file in output directory
        for i, solution in enumerate(solutions):
            num_digits = len(str(len(solutions) - 1))
            output_path = output_dir / f"{puzzle_name}.solution.{i:0{num_digits}d}.txt"
            with open(output_path, "w") as f:
                f.write(pformat(solution))

        logging.info(
            f"All {len(solutions)} solutions written to directory: '{output_dir}'"
        )


if __name__ == "__main__":
    main()
