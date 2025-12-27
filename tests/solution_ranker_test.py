from unittest.mock import AsyncMock, Mock

import pytest

from strands_solver.common import Puzzle, Solution, Strand
from strands_solver.solution_ranker import SolutionRanker


@pytest.mark.asyncio
async def test_find_best():
    embedder = Mock()
    embedder.get_embeddings = AsyncMock(
        return_value={
            "theme": [1.0, 0.0, 0.0],
            "CAT": [0.9, 0.1, 0.0],  # Similar to theme
            "DOG": [0.8, 0.2, 0.0],  # Similar to theme and CAT
            "XYZ": [0.0, 0.0, 1.0],  # Dissimilar to everything
            "ABC": [0.0, 0.0, 0.9],  # Similar to XYZ but dissimilar to others
        }
    )

    ranker = SolutionRanker(embedder)
    puzzle = Puzzle(name="test", theme="theme", grid=[["X"]], num_words=2)

    # Solution with semantically similar words
    solution1 = Solution(
        spangram=(Strand(positions=((0, 0),), string="CAT"),),
        non_spangram_strands=frozenset({Strand(positions=((1, 0),), string="DOG")}),
    )
    # Solution with semantically dissimilar words
    solution2 = Solution(
        spangram=(Strand(positions=((0, 0),), string="XYZ"),),
        non_spangram_strands=frozenset({Strand(positions=((1, 0),), string="ABC")}),
    )

    best = await ranker.find_best([solution1, solution2], puzzle)
    assert best == solution1
