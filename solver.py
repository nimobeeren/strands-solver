import logging

from common import Strand
from grid_coverer import GridCoverer
from word_finder import WordFinder

logger = logging.getLogger(__name__)


class Solver:
    def __init__(self, grid: list[list[str]]):
        self.grid = grid

    def solve(self) -> list[Strand] | None:
        """Solve the puzzle by finding all words in the grid and then finding the words
        which exactly cover the grid.

        Returns a list of strands covering the grid or None if unsatisfiable.
        """

        logger.info("Finding all words")
        finder = WordFinder(grid=self.grid)
        words = finder.find_all_words()
        logger.info(f"Found {len(words)} words")

        logger.info("Covering grid")
        coverer = GridCoverer(grid=self.grid, strands=words)
        solution = coverer.cover()
        logger.info("Covered grid")

        return solution
