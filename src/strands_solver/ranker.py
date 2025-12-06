from typing import Iterable

from .common import Solution


class Ranker:
    """Ranks solutions."""

    def find_best(self, solutions: Iterable[Solution]) -> Solution | None:
        # Return solution with spangram consisting of fewest number of words
        ranked = sorted(solutions, key=lambda s: len(s.spangram))
        return ranked[0]
