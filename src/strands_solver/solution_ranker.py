from itertools import combinations
import logging

import numpy as np

from .common import Puzzle, Solution
from .embedder import Embedder

logger = logging.getLogger(__name__)


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    arr1 = np.array(vec1)
    arr2 = np.array(vec2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(arr1, arr2) / (norm1 * norm2))


def _avg_word_similarity(
    solution: Solution, theme: str, embeddings: dict[str, list[float]]
) -> float:
    words = [theme]
    words += [strand.string for strand in solution.spangram]
    words += [strand.string for strand in solution.non_spangram_strands]

    similarities = [
        _cosine_similarity(embeddings[w1], embeddings[w2])
        for w1, w2 in combinations(words, 2)
    ]
    return sum(similarities) / len(similarities) if similarities else 0.0


class SolutionRanker:
    def __init__(self, embedder: Embedder) -> None:
        self.embedder = embedder

    async def find_best(
        self, solutions: list[Solution], puzzle: Puzzle
    ) -> Solution | None:
        """Find the best solution by average word similarity."""
        if not solutions:
            return None

        all_words = set[str]()
        for solution in solutions:
            for strand in solution.spangram:
                all_words.add(strand.string)
            for strand in solution.non_spangram_strands:
                all_words.add(strand.string)

        logging.info(f"Getting cached embeddings for {len(all_words)} words")
        embeddings = await self.embedder.get_embeddings(list(all_words), cached=True)
        logging.info("Embedding theme via API")
        theme_embedding = await self.embedder.get_embeddings(
            [puzzle.theme], cached=False
        )
        embeddings.update(theme_embedding)
        logging.info("Got all embeddings")

        logging.info(f"Computing similarity scores for {len(solutions)} solutions")
        best = max(
            solutions,
            key=lambda s: _avg_word_similarity(s, puzzle.theme, embeddings),
        )
        logging.info("Finished computing similarity scores")

        return best
