from nltk.corpus import words


class Solver:
    def __init__(self, grid: list[list[str]], rows=6, cols=8):
        self.grid = grid
        self.rows = rows
        self.cols = cols
        self.wordlist = [word.upper() for word in words.words()]

    def find_words(self, *, x: int, y: int, prefix="") -> set[str]:
        """Finds the words you can make when starting with the prefix and
        continuing at position (x, y)."""
        words: set[str] = set()
        candidate = prefix + self.grid[x][y]
        # print(f"Candidate: {candidate}")
        if not self.is_word_prefix(candidate):
            # print("Not a prefix")
            return words
        if self.is_word(candidate):
            print(f"Found word: {candidate}")
            words.add(candidate)

        next_xy_options = [
            [x + 1, y],  # right
            [x + 1, y + 1],  # down-right
            [x, y + 1],  # down
            [x - 1, y + 1],  # down-left
            [x - 1, y],  # left
            [x - 1, y - 1],  # up-left
            [x, y - 1],  # up
            [x + 1, y - 1],  # up-right
        ]

        for [nx, ny] in next_xy_options:
            # if coordinates are within bounds
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                words = words.union(self.find_words(x=nx, y=ny, prefix=candidate))

        return words

    def is_word(self, candidate: str):
        return candidate in self.wordlist

    def is_word_prefix(self, candidate: str):
        for word in self.wordlist:
            if word.startswith(candidate):
                return True
        return False
