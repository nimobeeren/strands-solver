import logging

from common import Strand
from grid_coverer import GridCoverer
from word_finder import WordFinder

logger = logging.getLogger(__name__)


class Solver:
    def __init__(self, grid: list[list[str]]):
        self.grid = grid

    def solve(self) -> list[list[Strand]]:
        """Solve the puzzle by finding all words in the grid and then finding all ways
        to exactly cover the grid with those words.

        Returns a list of solutions, where each solution is a list of strands covering
        the grid.
        """

        logger.info("Finding all words")
        finder = WordFinder(grid=self.grid)
        words = finder.find_all_words()
        logger.info(f"Found {len(words)} words")

        logger.info("Covering grid")
        coverer = GridCoverer(grid=self.grid, strands=words)
        solutions = coverer.cover()
        logger.info("Covered grid")

        return solutions
