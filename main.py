import argparse
import logging
import shutil
from pathlib import Path
from pprint import pformat

from coverer import Coverer
from finder import Finder
from ocr import load_grid_from_csv
from solver import Solver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("grid", type=str)
    args = parser.parse_args()

    grid = load_grid_from_csv(args.grid)

    logger.info("Solving puzzle:")
    for row in grid:
        logger.info(" ".join(row))

    finder = Finder(grid)
    coverer = Coverer(grid)
    solver = Solver(grid, finder=finder, coverer=coverer)
    solutions = solver.solve()

    if solutions:
        logging.info(f"First solution:\n{pformat(solutions[0])}")

        # Write each solution to its own file in out/ directory
        output_dir = Path("out")
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir()

        puzzle_name = Path(args.grid).stem

        for i, solution in enumerate(solutions):
            output_path = output_dir / f"{puzzle_name}.solution.{i}.txt"
            with open(output_path, "w") as f:
                f.write(pformat(solution))

        logging.info(f"Solutions written to '{output_dir}' directory")
