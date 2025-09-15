from enum import Enum

from nltk.corpus import words


class Direction(Enum):
    RIGHT = (1, 0)
    DOWN_RIGHT = (1, 1)
    DOWN = (0, 1)
    DOWN_LEFT = (-1, 1)
    LEFT = (-1, 0)
    UP_LEFT = (-1, -1)
    UP = (0, -1)
    UP_RIGHT = (1, -1)


class Solver:
    def __init__(self, grid: list[list[str]], rows=6, cols=8):
        self.grid = grid
        self.rows = rows
        self.cols = cols
        self.wordlist = [word.upper() for word in words.words()]

    def find_words(self, *, pos: tuple[int, int], prefix="", min_length=4) -> set[str]:
        """Finds the words you can make when starting with `prefix` and continuing at
        position `pos`."""
        words: set[str] = set()
        x, y = pos
        candidate = prefix + self.grid[x][y]
        if not self.is_word_prefix(candidate):
            return words
        if self.is_word(candidate) and len(candidate) >= min_length:
            print(f"Found word: {candidate}")
            words.add(candidate)

        for dir in Direction:
            # if coordinates are within bounds
            dx, dy = dir.value
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                words = words.union(
                    self.find_words(
                        pos=(nx, ny), prefix=candidate, min_length=min_length
                    )
                )

        return words

    def is_word(self, candidate: str):
        return candidate in self.wordlist

    def is_word_prefix(self, candidate: str):
        for word in self.wordlist:
            if word.startswith(candidate):
                return True
        return False
