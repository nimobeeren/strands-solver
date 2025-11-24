from itertools import combinations

from .common import Cover, Solution, Strand


class SpangramFinder:
    """Finds solutions with a spangram given a set of covers."""

    def __init__(
        self,
        grid: list[list[str]],
        *,
        num_words: int,
        spangram_max_words=5,
    ):
        """
        Parameters:
        - grid: The grid of the puzzle
        - num_words: The total number of words the solution should consist of (counting
            a concatenated spangram as one word).
        - spangram_max_words: The maximum number of words that can be concatenated to
            form a spangram. We assume there is a limit to this because finding all
            solutions would take a long time when allowing cases where the spangram
            consists of many short words.
        """
        self.grid = grid
        self.num_words = num_words
        self.spangram_max_words = spangram_max_words

        self.num_rows = len(grid)
        self.num_cols = len(grid[0])

    def find_spangrams(self, covers: set[Cover]) -> set[Solution]:
        """
        Finds all solutions, each consisting of only the strands in one of the given
        covers. Only the spangram may consist of a concatenation of several strands in
        one of the covers.
        """
        # Identify duplicate words across all covers
        all_strands = set()
        for cover in covers:
            all_strands |= cover

        words_by_string: dict[str, list[Strand]] = {}
        for strand in all_strands:
            if strand.string not in words_by_string:
                words_by_string[strand.string] = []
            words_by_string[strand.string].append(strand)

        # A word is a duplicate if it appears with different position sets
        duplicate_strings = set()
        for word_string, strands in words_by_string.items():
            if len(strands) > 1:
                position_sets = [frozenset(strand.positions) for strand in strands]
                if len(set(position_sets)) > 1:
                    duplicate_strings.add(word_string)

        # Find covers which have the correct number of words
        solutions = set[Solution]()

        for cover in covers:
            # If cover doesn't have enough words, it can never be a valid solution, so
            # skip it
            if len(cover) < self.num_words:
                continue
            # If a cover has exactly enough words, we don't need to concatenate
            # any words
            elif len(cover) == self.num_words:
                # For every spangram in the cover, add a solution with that spangram
                for strand in cover:
                    if strand.is_spangram(self.num_rows, self.num_cols):
                        solution = Solution(
                            spangram=(strand,),
                            non_spangram_strands=frozenset(cover - {strand}),
                        )
                        solutions.add(solution)

            # If a cover has too many words, we may be able to reduce the number by
            # concatenating some words (note: only the spangram can be a concatenation)
            elif len(cover) > self.num_words:
                # Number of words that need to be concatenated into one
                K = len(cover) - self.num_words + 1

                # We assume there is a limit to how many words a spangram consists of
                # in real solutions, and since we require concatenation of more words
                # than that, this can't be a real solution.
                if K > self.spangram_max_words:
                    continue

                # Optimization: we only try concatenations that include all duplicate
                # words (words that can be formed in multiple positions in the grid),
                # since real solutions never contain duplicate words except
                # when concatenated.

                # Identify duplicates in this cover
                duplicates_in_cover = [
                    strand for strand in cover if strand.string in duplicate_strings
                ]
                D = len(duplicates_in_cover)

                # If there are more duplicates than words to concatenate, we can't
                # include all duplicates in the concatenation. Therefore, this cover
                # can never be a real solution.
                if D > K:
                    continue

                # Build adjacency graph: map each word to words that can follow it
                cover_list = list(cover)
                adjacency = {}
                for word in cover_list:
                    adjacency[word] = [
                        other
                        for other in cover_list
                        if word != other and word.can_concatenate(other)
                    ]

                if D == 0:
                    # No duplicates, need to try all K-length orderings of words in
                    # the cover
                    for words_to_concat in combinations(cover, K):
                        for ordering in self._find_orderings(
                            words_to_concat, adjacency
                        ):
                            concatenated = ordering[0].concatenate(*ordering[1:])
                            if (
                                concatenated.is_spangram(self.num_rows, self.num_cols)
                                # The concatenated strand may cross itself at the word
                                # border, but this doesn't happen in real solutions
                                and not concatenated.has_self_crossing()
                            ):
                                solution = Solution(
                                    spangram=ordering,
                                    non_spangram_strands=frozenset(
                                        cover - set(words_to_concat)
                                    ),
                                )
                                solutions.add(solution)
                else:
                    # Only try combinations that include all duplicates
                    non_duplicates = [
                        strand for strand in cover if strand not in duplicates_in_cover
                    ]

                    # Need to choose (K - D) non-duplicates to go with D duplicates
                    num_non_duplicates_needed = K - D

                    if num_non_duplicates_needed == 0:
                        # All words to concatenate are duplicates
                        words_to_concat = tuple(duplicates_in_cover)
                        for ordering in self._find_orderings(
                            words_to_concat, adjacency
                        ):
                            concatenated = ordering[0].concatenate(*ordering[1:])
                            if concatenated.is_spangram(self.num_rows, self.num_cols):
                                solution = Solution(
                                    spangram=ordering,
                                    non_spangram_strands=frozenset(
                                        cover - set(words_to_concat)
                                    ),
                                )
                                solutions.add(solution)
                    else:
                        # Try combinations of non-duplicates with all duplicates
                        for non_dup_combo in combinations(
                            non_duplicates, num_non_duplicates_needed
                        ):
                            words_to_concat = tuple(duplicates_in_cover) + non_dup_combo
                            for ordering in self._find_orderings(
                                words_to_concat, adjacency
                            ):
                                concatenated = ordering[0].concatenate(*ordering[1:])
                                if concatenated.is_spangram(
                                    self.num_rows, self.num_cols
                                ):
                                    solution = Solution(
                                        spangram=ordering,
                                        non_spangram_strands=frozenset(
                                            cover - set(words_to_concat)
                                        ),
                                    )
                                    solutions.add(solution)

        return solutions

    def _find_orderings(
        self, words: tuple[Strand, ...], adjacency: dict[Strand, list[Strand]]
    ) -> list[tuple[Strand, ...]]:
        """Find all valid orderings of words where consecutive words can be concatenated.

        Uses the adjacency graph to only generate orderings where each word can
        concatenate with the next, avoiding the need to try all permutations.
        """
        result = []
        words_set = set(words)

        # Try starting from each word
        for start_word in words:
            # Build chains starting from this word using DFS
            self._build_chains_recursive(
                current_chain=[start_word],
                remaining=words_set - {start_word},
                adjacency=adjacency,
                result=result,
            )

        return result

    def _build_chains_recursive(
        self,
        current_chain: list[Strand],
        remaining: set[Strand],
        adjacency: dict[Strand, list[Strand]],
        result: list[tuple[Strand, ...]],
    ):
        """Recursively build valid chains of words using depth-first search."""
        if not remaining:
            # We've used all words in this combination, add this chain to results
            result.append(tuple(current_chain))
            return

        last_word = current_chain[-1]
        # Only try extending with words that can actually follow the last word
        for next_word in adjacency[last_word]:
            if next_word in remaining:
                current_chain.append(next_word)
                self._build_chains_recursive(
                    current_chain,
                    remaining - {next_word},
                    adjacency,
                    result,
                )
                current_chain.pop()  # backtrack
