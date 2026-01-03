import logging

import numpy as np
import numpy.typing as npt

from .common import Puzzle, Solution
from .embedder import Embedder

logger = logging.getLogger(__name__)


class SolutionRanker:
    def __init__(self, embedder: Embedder) -> None:
        self.embedder = embedder
        self._theme: str
        self._word_to_idx: dict[str, int]
        self._similarity_matrix: npt.NDArray[np.float32]

    def _init_similarity_matrix(
        self, embeddings: dict[str, npt.NDArray[np.float32]], theme: str
    ) -> None:
        self._theme = theme
        # Sort words for consistent ordering across solutions with same word set
        words = sorted(embeddings.keys())
        self._word_to_idx = {w: i for i, w in enumerate(words)}

        # Compute normalized similarity matrix once
        X = np.stack([embeddings[w] for w in words])
        norms = np.linalg.norm(X, axis=1, keepdims=True).astype(np.float32)
        norms = np.where(norms == 0, np.float32(1.0), norms)
        X = X / norms
        self._similarity_matrix = (X @ X.T).astype(np.float32)

    def _avg_word_similarity(self, solution: Solution) -> float:
        # Get sorted indices for this solution's words
        word_set = {self._theme}
        word_set |= {strand.string for strand in solution.spangram}
        word_set |= {strand.string for strand in solution.non_spangram_strands}
        indices = sorted(self._word_to_idx[w] for w in word_set)

        total = 0.0
        count = 0
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                total += self._similarity_matrix[indices[i], indices[j]]
                count += 1
        return total / count

    def _spangram_word_count(self, solution: Solution) -> int:
        return len(solution.spangram)

    def _avg_spangram_similarity(self, solution: Solution) -> float:
        # Get sorted indices for this solution's words
        word_set = {self._theme}
        word_set |= {strand.string for strand in solution.spangram}
        word_set |= {strand.string for strand in solution.non_spangram_strands}
        indices = sorted(self._word_to_idx[w] for w in word_set)

        spangram_indices = [
            self._word_to_idx[strand.string] for strand in solution.spangram
        ]
        total = 0.0
        count = 0
        for si in spangram_indices:
            for idx in indices:
                if si != idx:
                    total += self._similarity_matrix[si, idx]
                    count += 1
        return total / count if count > 0 else 0.0

    async def rank(self, solutions: list[Solution], puzzle: Puzzle) -> list[Solution]:
        """Ranks solutions from best to worst.

        Ranking criteria (in order of priority):
        1. Higher average inter-word similarity
        2. Fewer spangram words
        3. Higher average spangram-to-other-word similarity
        """
        if not solutions:
            return []

        all_words = set[str]()
        for solution in solutions:
            for strand in solution.spangram:
                all_words.add(strand.string)
            for strand in solution.non_spangram_strands:
                all_words.add(strand.string)

        logger.info(f"Getting embeddings for {len(all_words)} words + theme")
        all_contents = list(all_words) + [puzzle.theme]
        embeddings = await self.embedder.get_embeddings(all_contents)
        logger.info("Got embeddings")

        logger.info(
            f"Computing similarity matrix for {len(embeddings)} embeddings + theme"
        )
        self._init_similarity_matrix(embeddings, puzzle.theme)
        logger.info("Computed similarity matrix")

        logger.info(f"Sorting {len(solutions)} solutions")
        ranked = sorted(
            solutions,
            key=lambda s: (
                -self._avg_word_similarity(s),
                self._spangram_word_count(s),
                -self._avg_spangram_similarity(s),
            ),
        )
        logger.info("Sorted solutions")
        return ranked
