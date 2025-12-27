import logging

import numpy as np
import numpy.typing as npt

from .common import Puzzle, Solution
from .embedder import Embedder

logger = logging.getLogger(__name__)


def _avg_word_similarity(
    solution: Solution,
    theme: str,
    embeddings: dict[str, npt.NDArray[np.float32]],
) -> float:
    words = [theme]
    words += [strand.string for strand in solution.spangram]
    words += [strand.string for strand in solution.non_spangram_strands]

    if len(words) < 2:
        raise ValueError("At least two words are required to compute similarity")

    # Compute cosine similarity for all pairs of words
    X = np.stack([embeddings[w] for w in words])
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)  # avoid division by zero
    X = X / norms
    S = X @ X.T

    i_upper, j_upper = np.triu_indices(len(words), k=1)
    upper_values = S[i_upper, j_upper]
    return float(np.mean(upper_values))


class SolutionRanker:
    def __init__(self, embedder: Embedder) -> None:
        self.embedder = embedder

    async def rank(self, solutions: list[Solution], puzzle: Puzzle) -> list[Solution]:
        """Rank solutions by average word similarity, from best to worst."""
        if not solutions:
            return []

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
        ranked = sorted(
            solutions,
            key=lambda s: _avg_word_similarity(s, puzzle.theme, embeddings),
            reverse=True,
        )
        logging.info("Finished computing similarity scores")

        return ranked
