import logging

from .common import Puzzle, Solution
from .embedder import Embedder
from .grid_coverer import GridCoverer
from .solution_ranker import SolutionRanker
from .spangram_finder import SpangramFinder
from .word_finder import WordFinder

logger = logging.getLogger(__name__)


class Solver:
    def __init__(
        self,
        puzzle: Puzzle,
        *,
        finder: WordFinder | None = None,
        coverer: GridCoverer | None = None,
        spangram_finder: SpangramFinder | None = None,
        ranker: SolutionRanker | None = None,
    ):
        self._puzzle = puzzle
        self._finder = finder or WordFinder(puzzle.grid)
        self._coverer = coverer or GridCoverer(puzzle.grid)
        self._spangram_finder = spangram_finder or SpangramFinder(
            puzzle.grid, num_words=puzzle.num_words
        )
        self._ranker = ranker or SolutionRanker(Embedder())

    def find_all_solutions(self) -> set[Solution]:
        """Returns a set of solutions, where each solution is a set of strands covering
        the grid including at least one spangram. The solutions are not ranked.
        """
        logger.info("Finding words")
        words = self._finder.find_all_words()
        logger.info(f"Found {len(words)} words")

        logger.info("Covering grid")
        covers = self._coverer.cover(words)
        logger.info(f"Found {len(covers)} covers")

        logger.info("Finding spangrams")
        solutions = self._spangram_finder.find_spangrams(covers)
        logger.info(f"Found {len(solutions)} solutions with spangrams")

        return solutions

    async def solve(self) -> list[Solution]:
        """Solve the puzzle and return all solutions, ranked from best to worst.

        If ranking is not possible (embeddings database not available), returns
        solutions in arbitrary order.
        """
        can_rank = await self._ranker.can_rank()
        if not can_rank:
            logger.warning(
                "Cannot perform solution ranking due to missing GEMINI_API_KEY or "
                "incomplete dictionary embeddings database. "
                "To solve this, set the GEMINI_API_KEY environment variable and "
                "see README.md for instructions on generating dictionary embeddings. "
                "Without ranking, we cannot accurately determine the best solution, "
                "but we can still find all solutions."
            )

        solutions = self.find_all_solutions()
        if can_rank:
            solutions = await self._ranker.rank(list(solutions), self._puzzle)
        else:
            solutions = list(solutions)
        return solutions
