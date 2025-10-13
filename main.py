import argparse
import json
import logging
import shutil
from pathlib import Path
from pprint import pformat

from coverer import Coverer
from draw import draw
from finder import Finder
from solver import Solver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "puzzle", type=str, help="Path to a JSON file containing a puzzle"
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
    solver = Solver(grid, finder=finder, coverer=coverer, num_words=num_words)
    solutions = list(solver.solve())

    if solutions:
        logging.info("First solution:\n")
        draw(grid, solutions[0])
        print()
        for strand in solutions[0]:
            print(f"- {strand.string}")
        print()

        # Write each solution to its own file in out/ directory
        output_dir = Path("out")
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir()

        puzzle_name = Path(args.puzzle).stem

        for i, solution in enumerate(solutions):
            output_path = output_dir / f"{puzzle_name}.solution.{i}.txt"
            with open(output_path, "w") as f:
                f.write(pformat(solution))

        logging.info(f"All {len(solutions)} solutions written to '{output_dir}' directory")
