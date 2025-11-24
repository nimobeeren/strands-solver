import logging

from .common import Solution
from .coverer import Coverer
from .finder import Finder
from .spangram_finder import SpangramFinder

logger = logging.getLogger(__name__)


class Solver:
    def __init__(
        self,
        *,
        finder: Finder,
        coverer: Coverer,
        spangram_finder: SpangramFinder,
    ):
        self.finder = finder
        self.coverer = coverer
        self.spangram_finder = spangram_finder

    def solve(self) -> set[Solution]:
        """Solve the puzzle by finding all words in the grid and then finding all ways
        to exactly cover the grid with those words.

        Returns a set of solutions, where each solution is a set of strands covering
        the grid including at least one spangram.
        """

        logger.info("Finding words")
        words = self.finder.find_all_words()
        logger.info(f"Found {len(words)} words")

        logger.info("Covering grid")
        covers = self.coverer.cover(words)
        logger.info(f"Found {len(covers)} covers")

        logger.info("Finding spangrams")
        solutions = self.spangram_finder.find_spangrams(covers)
        logger.info(f"Found {len(solutions)} solutions with spangrams")

        return solutions
