import bisect
from dataclasses import dataclass
from enum import Enum

from dictionary import load_dictionary


class Direction(Enum):
    RIGHT = (1, 0)
    DOWN_RIGHT = (1, 1)
    DOWN = (0, 1)
    DOWN_LEFT = (-1, 1)
    LEFT = (-1, 0)
    UP_LEFT = (-1, -1)
    UP = (0, -1)
    UP_RIGHT = (1, -1)


@dataclass
class Strand:
    positions: list[tuple[int, int]]
    """Sequence of positions that the strand occupies."""
    string: str
    """String formed by concatenating the letters in the grid at each position."""

    def overlaps(self, other: "Strand"):
        return len(set(self.positions) & set(other.positions)) > 0


class Solver:
    def __init__(
        self,
        grid: list[list[str]],
        *,
        dictionary: set[str] | None = None,
    ):
        self.grid = grid
        self.num_rows = len(grid)
        self.num_cols = len(grid[0])
        self.num_cells = self.num_rows * self.num_cols

        print("Loading wordset")
        if dictionary is None:
            dictionary = load_dictionary()
        self.dictionary = dictionary
        self.sorted_dictionary = sorted(dictionary)
        print(f"Loaded {len(dictionary)} words")

    def solve(self) -> list[Strand] | None:
        """Solve the puzzle by finding all words in the grid and then finding the words
        which exactly cover the grid.

        This implementation uses a bitset-based exact-cover style search with MRV:
        - Represent the grid coverage as a 48-bit mask (one bit per cell)
        - For each candidate `Strand`, precompute a bit mask of its covered cells
        - At each step, choose the uncovered cell with the fewest available candidates (MRV)
        - Branch only on words that cover that cell and do not overlap already covered cells

        Returns a collection of `Strand`s covering the grid or None if unsatisfiable.
        """
        print("Finding all words")
        words = self.find_all_words()
        print(f"Found {len(words)} words")

        word_masks, cell_to_words = self.build_indices(words)

        # Core MRV backtracking using bitsets
        solution_indices = self.cover(
            word_masks=word_masks, cell_to_words=cell_to_words
        )

        if solution_indices is None:
            return None

        # Map indices back to Strands
        return [words[i] for i in solution_indices]

    def find_all_words(self) -> list[Strand]:
        """Finds all strands forming words in the grid."""
        words: list[Strand] = []
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                words += self.find_words(current_pos=(x, y))
        return words

    def find_words(
        self,
        *,
        current_pos: tuple[int, int],
        prefix: Strand = Strand(positions=[], string=""),
        min_length=4,
    ) -> list[Strand]:
        """Finds strands forming words in the grid starting with the `prefix` strand and
        continuing at `current_pos` without overlapping with the `prefix` strand."""
        words: list[Strand] = []
        x, y = current_pos

        # Create a candidate strand by taking the prefix strand and adding the letter at `current_pos` to it
        candidate = Strand(
            positions=prefix.positions + [(x, y)],
            string=prefix.string + self.grid[y][x],
        )

        if not self.is_word_prefix(candidate.string):
            return words

        if len(candidate.string) >= min_length and self.is_word(candidate.string):
            print(f"Found word: {candidate.string}")
            words.append(candidate)

        for dir in Direction:
            dx, dy = dir.value
            next_x, next_y = (x + dx, y + dy)

            if (
                next_x < 0
                or next_x >= self.num_cols
                or next_y < 0
                or next_y >= self.num_rows
            ):
                continue  # next position is out of bounds
            if (next_x, next_y) in candidate.positions:
                continue  # next position overlaps

            words += self.find_words(
                current_pos=(next_x, next_y),
                prefix=candidate,
                min_length=min_length,
            )

        return words

    def is_word(self, candidate: str) -> bool:
        return candidate in self.dictionary

    def is_word_prefix(self, candidate: str) -> bool:
        candidate = candidate.upper()
        i = bisect.bisect_left(self.sorted_dictionary, candidate)
        return i < len(self.sorted_dictionary) and self.sorted_dictionary[i].startswith(
            candidate
        )

    def build_indices(self, words: list[Strand]):
        """Computes:
        - `word_masks`: bit mask per word (1 bit per grid cell it covers)
        - `cell_to_words`: for each cell index, list of word indices that cover it
        """
        word_masks: list[int] = []
        cell_to_words: list[list[int]] = [[] for _ in range(self.num_cells)]

        for i, strand in enumerate(words):
            mask = 0
            for x, y in strand.positions:
                bit_index = y * self.num_cols + x
                mask |= 1 << bit_index
                cell_to_words[bit_index].append(i)
            word_masks.append(mask)

        return word_masks, cell_to_words

    def cover(
        self,
        *,
        word_masks: list[int],
        cell_to_words: list[list[int]],
        covered_mask: int = 0,
    ) -> list[int] | None:
        """Backtracking search that covers all cells exactly once using MRV branching.

        Returns a list of word indices forming a cover, or None if no cover exists.
        """
        # If fully covered, we are done
        all_cells_mask = (1 << self.num_cells) - 1
        if covered_mask == all_cells_mask:
            return []

        num_cells = self.num_rows * self.num_cols

        # MRV: choose the uncovered cell with the fewest available non-overlapping words
        best_candidates: list[int] | None = None

        for cell_index in range(num_cells):
            if (covered_mask >> cell_index) & 1:
                continue  # already covered

            candidates = [
                w_idx
                for w_idx in cell_to_words[cell_index]
                if (word_masks[w_idx] & covered_mask) == 0
            ]

            if not candidates:
                return None  # dead end: uncovered cell has no valid words

            if best_candidates is None or len(candidates) < len(best_candidates):
                best_candidates = candidates
                if len(best_candidates) == 1:
                    break  # small early exit when forced

        assert best_candidates is not None

        # Try candidates for the most constrained cell
        for w_idx in best_candidates:
            new_mask = covered_mask | word_masks[w_idx]
            result = self.cover(
                word_masks=word_masks,
                cell_to_words=cell_to_words,
                covered_mask=new_mask,
            )
            if result is not None:
                return [w_idx] + result

        return None
