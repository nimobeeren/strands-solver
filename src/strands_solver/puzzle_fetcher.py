import datetime
from functools import lru_cache
from typing import Any

import httpx

from .common import Puzzle, Solution, Strand


class PuzzleFetcher:
    """Fetches puzzles from the NY Times API."""

    @lru_cache
    def _fetch_data(self, date: datetime.date) -> dict[str, Any]:
        response = httpx.get(
            f"https://www.nytimes.com/svc/strands/v2/{date.isoformat()}.json"
        )
        response.raise_for_status()
        return response.json()

    def fetch_puzzle(self, date: datetime.date) -> Puzzle:
        data = self._fetch_data(date)

        grid = []
        for row in data["startingBoard"]:
            grid.append([letter for letter in row])

        return Puzzle(
            name=date.isoformat(),
            theme=data["clue"],
            grid=grid,
            num_words=len(data["themeWords"]) + 1,  # +1 for spangram
        )

    def fetch_solution(self, date: datetime.date) -> Solution:
        """Fetches the official solution from the NY Times API.

        Note: This is not used for solving, only for verification/comparison.
        """
        data = self._fetch_data(date)

        grid = []
        for row in data["startingBoard"]:
            grid.append([letter for letter in row])

        def coords_to_strand(word: str, coords: list[list[int]]) -> Strand:
            # API returns [row, col], convert to (col, row) = (x, y)
            positions = tuple((col, row) for row, col in coords)
            return Strand(positions=positions, string=word)

        # Build spangram strand
        spangram_coords = data["spangramCoords"]
        spangram_word = "".join(grid[row][col] for row, col in spangram_coords)
        spangram = coords_to_strand(spangram_word, spangram_coords)

        # Build theme word strands
        theme_strands: set[Strand] = set()
        for word, coords in data["themeCoords"].items():
            theme_strands.add(coords_to_strand(word, coords))

        return Solution(
            spangram=(spangram,), non_spangram_strands=frozenset(theme_strands)
        )
