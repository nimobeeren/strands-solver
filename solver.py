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
    def __init__(self, grid: list[list[str]], *, rows=6, cols=8):
        self.grid = grid
        self.rows = rows
        self.cols = cols
        self.wordlist = [word.upper() for word in words.words()]

    def find_words(
        self,
        *,
        current_pos: tuple[int, int],
        prefix_pos: list[tuple[int, int]] = [],
        prefix_str="",
        min_length=4,
    ) -> set[str]:
        """Finds words in the grid starting with `prefix_str` and continuing at
        `current_pos` without using any of the positions in `prefix_pos`."""
        words: set[str] = set()
        x, y = current_pos
        candidate = prefix_str + self.grid[x][y]
        if not self.is_word_prefix(candidate):
            return words
        if self.is_word(candidate) and len(candidate) >= min_length:
            print(f"Found word: {candidate}")
            words.add(candidate)

        for dir in Direction:
            dx, dy = dir.value
            next_x, next_y = (x + dx, y + dy)
            # Check that next position is within bounds
            if next_x < 0 or next_x >= self.cols or next_y < 0 or next_y >= self.rows:
                continue
            # Check that next position doesn't overlap
            if (next_x, next_y) in prefix_pos:
                continue
            # Next position is valid, continue finding words
            words |= self.find_words(
                current_pos=(next_x, next_y),
                prefix_pos=[*prefix_pos, (x, y)],
                prefix_str=candidate,
                min_length=min_length,
            )

        return words

    def is_word(self, candidate: str):
        return candidate in self.wordlist

    def is_word_prefix(self, candidate: str):
        for word in self.wordlist:
            if word.startswith(candidate):
                return True
        return False
