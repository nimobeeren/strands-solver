import argparse
import logging
from pprint import pformat

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

    solver = Solver(grid)
    solution = solver.solve()
    logger.info(f"Solution:\n{pformat(solution)}")
