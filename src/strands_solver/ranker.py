from typing import Iterable

from .common import Solution


class Ranker:
    """Ranks solutions."""

    def find_best(self, solutions: Iterable[Solution]) -> Solution | None:
        # Return solution with spangram consisting of fewest number of words
        best = None
        for solution in solutions:
            if best is None:
                best = solution
                continue
            if len(solution.spangram) < len(best.spangram):
                best = solution
        return best
