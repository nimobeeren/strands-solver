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
        covers = self.coverer.cover(words)
        logger.info(f"Found {len(covers)} covers")

        # Find covers which contain a single spangram
        solutions = []
        for cover in covers:
            num_spangrams = len(
                [
                    strand
                    for strand in cover
                    if strand.is_spangram(self.num_rows, self.num_cols)
                ]
            )
            if num_spangrams == 1:
                solutions.append(cover)
        logger.info(f"Found {len(solutions)} solutions")

        return solutions
