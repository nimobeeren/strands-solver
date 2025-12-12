import datetime

import httpx

from .common import Puzzle


class PuzzleFetcher:
    """Fetches puzzles from the NY Times API."""

    def fetch_puzzle(self, date: datetime.date) -> Puzzle:
        response = httpx.get(
            f"https://www.nytimes.com/svc/strands/v2/{date.isoformat()}.json"
        )
        response.raise_for_status()
        data = response.json()

        grid = []
        for row in data["startingBoard"]:
            grid.append([letter for letter in row])

        return Puzzle(
            name=date.isoformat(),
            theme=data["clue"],
            grid=grid,
            num_words=len(data["themeWords"]) + 1,  # +1 for spangram
        )
