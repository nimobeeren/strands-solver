import logging

from common import Strand
from coverer import Coverer
from finder import Finder

logger = logging.getLogger(__name__)


class Solver:
    def __init__(self, grid: list[list[str]], *, finder: Finder, coverer: Coverer):
        self.grid = grid
        self.finder = finder
        self.coverer = coverer
        self.num_rows = len(grid)
        self.num_cols = len(grid[0])

    def solve(self) -> list[list[Strand]]:
        """Solve the puzzle by finding all words in the grid and then finding all ways
        to exactly cover the grid with those words.

        Returns a list of solutions, where each solution is a list of strands covering
        the grid.
        """

        logger.info("Finding all words")
        words = self.finder.find_all_words()
        logger.info(f"Found {len(words)} words")

        logger.info("Covering grid")
        solutions = self.coverer.cover(words)
        logger.info(f"Found {len(solutions)} solutions before spangram check")

        solutions = [
            solution
            for solution in solutions
            if any(
                strand.is_spangram(self.num_rows, self.num_cols) for strand in solution
            )
        ]
        logger.info(f"Found {len(solutions)} solutions after spangram check")

        return solutions
