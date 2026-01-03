from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

from strands_solver.common import Puzzle, Solution, Strand
from strands_solver.embedder import ApiKeyError, EmbeddingNotFoundError
from strands_solver.solution_ranker import SolutionRanker


@pytest.mark.asyncio
async def test_rank_by_avg_similarity():
    """Solutions are ranked by average inter-word similarity."""
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


@pytest.mark.asyncio
async def test_rank_prefers_fewer_spangram_words():
    """When avg similarity is equal, prefer solutions with fewer spangram words."""
    embedder = Mock()
    # All words have the same embedding, so avg similarity is identical
    embedder.get_embeddings = AsyncMock(
        return_value={
            "theme": np.array([1.0, 0.0, 0.0], dtype=np.float32),
            "APPLE": np.array([1.0, 0.0, 0.0], dtype=np.float32),
            "SAUCE": np.array([1.0, 0.0, 0.0], dtype=np.float32),
            "PIE": np.array([1.0, 0.0, 0.0], dtype=np.float32),
        }
    )

    ranker = SolutionRanker(embedder)
    puzzle = Puzzle(name="test", theme="theme", grid=[["X"]], num_words=2)

    # Solution with 2-word spangram (APPLE + SAUCE)
    solution_2_words = Solution(
        spangram=(
            Strand(positions=((0, 0),), string="APPLE"),
            Strand(positions=((1, 0),), string="SAUCE"),
        ),
        non_spangram_strands=frozenset({Strand(positions=((2, 0),), string="PIE")}),
    )
    # Solution with 1-word spangram
    solution_1_word = Solution(
        spangram=(Strand(positions=((0, 0), (1, 0)), string="APPLE"),),
        non_spangram_strands=frozenset(
            {
                Strand(positions=((2, 0),), string="SAUCE"),
                Strand(positions=((3, 0),), string="PIE"),
            }
        ),
    )

    ranked = await ranker.rank([solution_2_words, solution_1_word], puzzle)
    assert ranked[0] == solution_1_word


@pytest.mark.asyncio
async def test_rank_prefers_higher_spangram_similarity():
    """When avg similarity and spangram word count are equal, prefer higher
    spangram-to-other-word similarity."""
    embedder = Mock()
    embedder.get_embeddings = AsyncMock(
        return_value={
            "theme": np.array([1.0, 0.0, 0.0], dtype=np.float32),
            # CENTRAL is similar to both RELATED1 and RELATED2
            "CENTRAL": np.array([0.8, 0.2, 0.0], dtype=np.float32),
            # RELATED1 and RELATED2 are similar to CENTRAL but less to each other
            "RELATED1": np.array([0.9, 0.1, 0.0], dtype=np.float32),
            "RELATED2": np.array([0.7, 0.3, 0.0], dtype=np.float32),
        }
    )

    ranker = SolutionRanker(embedder)
    puzzle = Puzzle(name="test", theme="theme", grid=[["X"]], num_words=2)

    # Same words in both solutions, just different spangram choice
    # CENTRAL as spangram has higher avg similarity to all other words
    solution_central_spangram = Solution(
        spangram=(Strand(positions=((0, 0),), string="CENTRAL"),),
        non_spangram_strands=frozenset(
            {
                Strand(positions=((1, 0),), string="RELATED1"),
                Strand(positions=((2, 0),), string="RELATED2"),
            }
        ),
    )
    # RELATED1 as spangram has lower avg similarity to all other words
    solution_related1_spangram = Solution(
        spangram=(Strand(positions=((1, 0),), string="RELATED1"),),
        non_spangram_strands=frozenset(
            {
                Strand(positions=((0, 0),), string="CENTRAL"),
                Strand(positions=((2, 0),), string="RELATED2"),
            }
        ),
    )

    ranked = await ranker.rank(
        [solution_related1_spangram, solution_central_spangram], puzzle
    )
    assert ranked[0] == solution_central_spangram


@pytest.mark.asyncio
async def test_rank_spangram_similarity_includes_other_spangram_words():
    """Spangram similarity is computed against all other words, including other
    spangram words in multi-word spangrams."""
    embedder = Mock()
    embedder.get_embeddings = AsyncMock(
        return_value={
            "theme": np.array([1.0, 0.0, 0.0], dtype=np.float32),
            # COLD and SYMPTOM are similar to each other
            "COLD": np.array([0.9, 0.1, 0.0], dtype=np.float32),
            "SYMPTOM": np.array([0.85, 0.15, 0.0], dtype=np.float32),
            # SNIFFLE and SNEEZE are less similar to each other
            "SNIFFLE": np.array([0.8, 0.2, 0.0], dtype=np.float32),
            "SNEEZE": np.array([0.6, 0.4, 0.0], dtype=np.float32),
            # Other words
            "COUGH": np.array([0.7, 0.3, 0.0], dtype=np.float32),
        }
    )

    ranker = SolutionRanker(embedder)
    puzzle = Puzzle(name="test", theme="theme", grid=[["X"]], num_words=2)

    # COLD+SYMPTOM spangram: each word is similar to theme, each other, and COUGH
    solution_coldsymptom = Solution(
        spangram=(
            Strand(positions=((0, 0),), string="COLD"),
            Strand(positions=((1, 0),), string="SYMPTOM"),
        ),
        non_spangram_strands=frozenset(
            {
                Strand(positions=((2, 0),), string="SNIFFLE"),
                Strand(positions=((3, 0),), string="SNEEZE"),
                Strand(positions=((4, 0),), string="COUGH"),
            }
        ),
    )
    # SNIFFLE+SNEEZE spangram: SNEEZE is less similar to other words
    solution_snifflesneeze = Solution(
        spangram=(
            Strand(positions=((2, 0),), string="SNIFFLE"),
            Strand(positions=((3, 0),), string="SNEEZE"),
        ),
        non_spangram_strands=frozenset(
            {
                Strand(positions=((0, 0),), string="COLD"),
                Strand(positions=((1, 0),), string="SYMPTOM"),
                Strand(positions=((4, 0),), string="COUGH"),
            }
        ),
    )

    # Both have same words (same avg similarity), same spangram count (2)
    # COLD+SYMPTOM should rank higher because each spangram word has higher
    # avg similarity to all other words (including the other spangram word)
    ranked = await ranker.rank([solution_snifflesneeze, solution_coldsymptom], puzzle)
    assert ranked[0] == solution_coldsymptom


@pytest.mark.asyncio
async def test_rank_raises_on_missing_embedding():
    embedder = Mock()
    embedder.get_embeddings = AsyncMock(
        side_effect=EmbeddingNotFoundError("Embedding not found for 'MISSING'")
    )
    ranker = SolutionRanker(embedder)
    puzzle = Puzzle(name="test", theme="theme", grid=[["X"]], num_words=2)

    solution = Solution(
        spangram=(Strand(positions=((0, 0),), string="CAT"),),
        non_spangram_strands=frozenset({Strand(positions=((1, 0),), string="DOG")}),
    )

    with pytest.raises(EmbeddingNotFoundError):
        await ranker.rank([solution], puzzle)


@pytest.mark.asyncio
async def test_rank_raises_on_api_key_missing():
    embedder = Mock()
    embedder.get_embeddings = AsyncMock(
        side_effect=ApiKeyError("GEMINI_API_KEY environment variable is not set")
    )
    ranker = SolutionRanker(embedder)
    puzzle = Puzzle(name="test", theme="theme", grid=[["X"]], num_words=2)

    solution = Solution(
        spangram=(Strand(positions=((0, 0),), string="CAT"),),
        non_spangram_strands=frozenset(),
    )

    with pytest.raises(ApiKeyError):
        await ranker.rank([solution], puzzle)
