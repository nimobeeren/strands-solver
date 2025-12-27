from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

from strands_solver.common import Puzzle, Solution, Strand
from strands_solver.solution_ranker import SolutionRanker


@pytest.mark.asyncio
async def test_rank():
    embedder = Mock()
    embedder.get_embeddings = AsyncMock(
        return_value={
            "theme": np.array([1.0, 0.0, 0.0], dtype=np.float32),
            "CAT": np.array([0.9, 0.1, 0.0], dtype=np.float32),  # Similar to theme
            "DOG": np.array(
                [0.8, 0.2, 0.0], dtype=np.float32
            ),  # Similar to theme and CAT
            "XYZ": np.array(
                [0.0, 0.0, 1.0], dtype=np.float32
            ),  # Dissimilar to everything
            "ABC": np.array(
                [0.0, 0.0, 0.9], dtype=np.float32
            ),  # Similar to XYZ but dissimilar to others
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

    ranked = await ranker.rank([solution1, solution2], puzzle)
    assert ranked == [solution1, solution2]
