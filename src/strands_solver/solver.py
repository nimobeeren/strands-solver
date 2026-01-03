import logging
from dataclasses import dataclass

from .common import Puzzle, Solution
from .embedder import ApiKeyError, EmbeddingNotFoundError, Embedder
from .grid_coverer import GridCoverer
from .solution_ranker import SolutionRanker
from .spangram_finder import SpangramFinder
from .word_finder import WordFinder

logger = logging.getLogger(__name__)


@dataclass
class SolverStats:
    """Statistics captured during solving."""

    num_words: int | None = None
    num_covers: int | None = None
    num_solutions: int | None = None


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
        self.stats = SolverStats()

    def find_all_solutions(self) -> set[Solution]:
        """Returns a set of solutions, where each solution is a set of strands covering
        the grid including at least one spangram. The solutions are not ranked.
        """
        logger.info("Finding words in grid")
        words = self._finder.find_all_words()
        self.stats.num_words = len(words)
        logger.info(f"Found {len(words)} words")

        logger.info("Covering grid with words")
        covers = self._coverer.cover(words)
        self.stats.num_covers = len(covers)
        logger.info(f"Found {len(covers)} covers")

        logger.info("Finding spangrams")
        solutions = self._spangram_finder.find_spangrams(covers)
        self.stats.num_solutions = len(solutions)
        logger.info(f"Found {len(solutions)} solutions with spangrams")

        return solutions

    async def solve(self) -> list[Solution]:
        """Solve the puzzle and return all solutions, ranked from best to worst.

        If ranking fails, logs a warning and returns solutions in arbitrary order.
        """
        solutions = self.find_all_solutions()
        try:
            logger.info(f"Ranking {len(solutions)} solutions")
            ranked = await self._ranker.rank(list(solutions), self._puzzle)
            logger.info("Ranked solutions")
            return ranked
        except (ApiKeyError, EmbeddingNotFoundError) as e:
            if isinstance(e, ApiKeyError):
                logger.warning(
                    "Cannot rank solutions due to missing/invalid GEMINI_API_KEY. "
                    "To fix this, set the GEMINI_API_KEY environment variable."
                )
            elif isinstance(e, EmbeddingNotFoundError):
                logger.warning(
                    f"Cannot rank solutions due to missing dictionary embeddings: {e} "
                    "See README.md for instructions on generating dictionary embeddings."
                )
            else:
                raise

            logger.warning(
                "Continuing without solution ranking. "
                "This means the best solution cannot be accurately determined."
            )
            return list(solutions)
