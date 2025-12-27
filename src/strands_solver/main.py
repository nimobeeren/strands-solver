import logging

from .common import Puzzle, Solution
from .embedder import Embedder
from .grid_coverer import GridCoverer
from .solution_ranker import SolutionRanker
from .solver import Solver
from .spangram_finder import SpangramFinder
from .word_finder import WordFinder


logger = logging.getLogger(__name__)


async def solve_puzzle(puzzle: Puzzle) -> list[Solution]:
    """
    Find solutions for a puzzle, ranked from best to worst.
    """
    finder = WordFinder(puzzle.grid)
    coverer = GridCoverer(puzzle.grid)
    spangram_finder = SpangramFinder(puzzle.grid, num_words=puzzle.num_words)
    solver = Solver(finder=finder, coverer=coverer, spangram_finder=spangram_finder)
    solutions = solver.solve()

    embedder = Embedder()
    ranker = SolutionRanker(embedder)
    return await ranker.rank(list(solutions), puzzle)
