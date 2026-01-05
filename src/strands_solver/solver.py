import logging
from dataclasses import dataclass

from .common import Puzzle, Solution, Strand
from .embedder import ApiKeyError, EmbeddingNotFoundError, Embedder
from .grid_coverer import GridCoverer
from .solution_ranker import SolutionRanker
from .spangram_finder import DEFAULT_MIN_WORD_LENGTH, SpangramFinder
from .word_finder import WordFinder

logger = logging.getLogger(__name__)


@dataclass
class SolverStats:
    """Statistics captured during solving."""

    num_words: int | None = None
    num_short_words: int | None = None
    num_covers: int | None = None
    num_solutions: int | None = None


class Solver:
    def __init__(
        self,
        puzzle: Puzzle,
        *,
        finder: WordFinder | None = None,
        short_word_finder: WordFinder | None = None,
        coverer: GridCoverer | None = None,
        spangram_finder: SpangramFinder | None = None,
        ranker: SolutionRanker | None = None,
    ):
        self._puzzle = puzzle
        self._finder = finder or WordFinder(puzzle.grid)
        # Use the finder's min_length to determine what's a "short word" that can only
        # be used in spangrams. This ensures that when a custom finder with min_length=1
        # is passed, all words are valid as non-spangram words.
        self._min_word_length = self._finder.min_length
        # Short word finder finds all words (min_length=1) for spangram consideration
        self._short_word_finder = short_word_finder or WordFinder(
            puzzle.grid,
            dictionary=self._finder.dictionary,
            min_length=1,
        )
        self._coverer = coverer or GridCoverer(puzzle.grid)
        self._spangram_finder = spangram_finder or SpangramFinder(
            puzzle.grid,
            num_words=puzzle.num_words,
            min_word_length=self._min_word_length,
        )
        self._ranker = ranker or SolutionRanker(Embedder())
        self.stats = SolverStats()

    def find_all_solutions(self) -> set[Solution]:
        """Returns a set of solutions, where each solution is a set of strands covering
        the grid including at least one spangram. The solutions are not ranked.
        """
        logger.info("Finding words in grid")
        regular_words = self._finder.find_all_words()
        self.stats.num_words = len(regular_words)
        logger.info(f"Found {len(regular_words)} regular words")

        # Find short words for spangram consideration
        all_words = self._short_word_finder.find_all_words()
        short_words = self._filter_short_words(all_words, regular_words)
        self.stats.num_short_words = len(short_words)
        if short_words:
            logger.info(f"Found {len(short_words)} short words for spangram")

        # Combine regular and short words for grid covering
        combined_words = regular_words | short_words

        logger.info("Covering grid with words")
        covers = self._coverer.cover(combined_words)
        self.stats.num_covers = len(covers)
        logger.info(f"Found {len(covers)} covers")

        logger.info("Finding spangrams")
        solutions = self._spangram_finder.find_spangrams(covers)
        self.stats.num_solutions = len(solutions)
        logger.info(f"Found {len(solutions)} solutions with spangrams")

        return solutions

    def _filter_short_words(
        self, all_words: set[Strand], regular_words: set[Strand]
    ) -> set[Strand]:
        """Returns words that are short (< min_word_length) and not already
        in regular_words."""
        return {
            w
            for w in all_words
            if len(w.string) < self._min_word_length and w not in regular_words
        }

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
