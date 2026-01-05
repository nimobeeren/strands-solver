from itertools import combinations

from .common import Cover, Solution, Strand

# Default minimum word length for non-spangram words
DEFAULT_MIN_WORD_LENGTH = 4


class SpangramFinder:
    """Finds solutions with a spangram given a set of covers."""

    def __init__(
        self,
        grid: list[list[str]],
        *,
        num_words: int,
        spangram_max_words: int = 5,
        min_word_length: int = DEFAULT_MIN_WORD_LENGTH,
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
        - min_word_length: Minimum length for non-spangram words. Words shorter than
            this can only appear as part of a concatenated spangram.
        """
        self._grid = grid
        self._num_words = num_words
        self._spangram_max_words = spangram_max_words
        self._min_word_length = min_word_length
        self._num_rows = len(grid)
        self._num_cols = len(grid[0])

    def _is_valid_concatenated_spangram(
        self, concatenated: Strand, non_spangram_strands: frozenset[Strand]
    ) -> bool:
        """Check if a concatenated (spangram) and non-spangram strands could form a
        valid solution."""
        return (
            concatenated.is_spangram(self._num_rows, self._num_cols)
            and not concatenated.has_self_crossing()
            # The concatenated strand cannot cross other (non-spangram) strands
            and not any(s for s in non_spangram_strands if concatenated.crosses(s))
        )

    def find_spangrams(self, covers: set[Cover]) -> set[Solution]:
        """
        Finds all solutions, each consisting of only the strands in one of the given
        covers. Only the spangram may consist of a concatenation of several strands in
        one of the covers.

        Equivalent solutions are deduplicated.
        """
        # Identify "spangram-only" words - words that can only appear as part of a
        # concatenated spangram, not as standalone non-spangram words. This includes:
        # 1. Duplicate words (appear in multiple positions in the grid)
        # 2. Short words (less than min_word_length)
        all_strands = set()
        for cover in covers:
            all_strands |= cover

        words_by_string: dict[str, list[Strand]] = {}
        for strand in all_strands:
            if strand.string not in words_by_string:
                words_by_string[strand.string] = []
            words_by_string[strand.string].append(strand)

        # A word is spangram-only if:
        # 1. It's a duplicate (appears with different position sets), OR
        # 2. It's shorter than min_word_length
        spangram_only_strings = set()
        for word_string, strands in words_by_string.items():
            # Check if it's a short word
            if len(word_string) < self._min_word_length:
                spangram_only_strings.add(word_string)
            # Check if it's a duplicate (appears in multiple positions)
            elif len(strands) > 1:
                position_sets = [frozenset(strand.positions) for strand in strands]
                if len(set(position_sets)) > 1:
                    spangram_only_strings.add(word_string)

        # Find covers which have the correct number of words
        solutions = set[Solution]()

        for cover in covers:
            # If cover doesn't have enough words, it can never be a valid solution, so
            # skip it
            if len(cover) < self._num_words:
                continue
            # If a cover has exactly enough words, we don't need to concatenate
            # any words
            elif len(cover) == self._num_words:
                # For every spangram in the cover, add a solution with that spangram
                # But only if no non-spangram strand is spangram-only
                for strand in cover:
                    if strand.is_spangram(self._num_rows, self._num_cols):
                        non_spangram_strands = cover - {strand}
                        # Check that no non-spangram strand is spangram-only
                        if any(
                            s.string in spangram_only_strings
                            for s in non_spangram_strands
                        ):
                            continue
                        solution = Solution(
                            spangram=(strand,),
                            non_spangram_strands=frozenset(non_spangram_strands),
                        )
                        solutions.add(solution)

            # If a cover has too many words, we may be able to reduce the number by
            # concatenating some words (note: only the spangram can be a concatenation)
            elif len(cover) > self._num_words:
                # Number of words that need to be concatenated into one
                K = len(cover) - self._num_words + 1

                # We assume there is a limit to how many words a spangram consists of
                # in real solutions, and since we require concatenation of more words
                # than that, this can't be a real solution.
                if K > self._spangram_max_words:
                    continue

                # Optimization: we only try concatenations that include all spangram-only
                # words (short words or words appearing in multiple positions), since
                # these can only appear as part of a concatenated spangram.

                # Identify spangram-only words in this cover
                spangram_only_in_cover = [
                    strand for strand in cover if strand.string in spangram_only_strings
                ]
                S = len(spangram_only_in_cover)

                # If there are more spangram-only words than words to concatenate, we
                # can't include all of them in the concatenation. Therefore, this cover
                # can never produce a valid solution.
                if S > K:
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

                if S == 0:
                    # No spangram-only words, need to try all K-length orderings of
                    # words in the cover
                    for words_to_concat in combinations(cover, K):
                        for ordering in self._find_orderings(
                            words_to_concat, adjacency
                        ):
                            concatenated = ordering[0].concatenate(*ordering[1:])
                            non_spangram = cover - set(words_to_concat)
                            if self._is_valid_concatenated_spangram(
                                concatenated, non_spangram
                            ):
                                solution = Solution(
                                    spangram=ordering,
                                    non_spangram_strands=frozenset(non_spangram),
                                )
                                solutions.add(solution)
                else:
                    # Only try combinations that include all spangram-only words
                    regular_words = [
                        strand
                        for strand in cover
                        if strand not in spangram_only_in_cover
                    ]

                    # Need to choose (K - S) regular words to go with S spangram-only
                    num_regular_needed = K - S

                    if num_regular_needed == 0:
                        # All words to concatenate are spangram-only
                        words_to_concat = tuple(spangram_only_in_cover)
                        for ordering in self._find_orderings(
                            words_to_concat, adjacency
                        ):
                            concatenated = ordering[0].concatenate(*ordering[1:])
                            non_spangram = cover - set(words_to_concat)
                            if self._is_valid_concatenated_spangram(
                                concatenated, non_spangram
                            ):
                                solution = Solution(
                                    spangram=ordering,
                                    non_spangram_strands=frozenset(non_spangram),
                                )
                                solutions.add(solution)
                    else:
                        # Try combinations of regular words with all spangram-only words
                        for regular_combo in combinations(
                            regular_words, num_regular_needed
                        ):
                            words_to_concat = (
                                tuple(spangram_only_in_cover) + regular_combo
                            )
                            for ordering in self._find_orderings(
                                words_to_concat, adjacency
                            ):
                                concatenated = ordering[0].concatenate(*ordering[1:])
                                non_spangram = cover - set(words_to_concat)
                                if self._is_valid_concatenated_spangram(
                                    concatenated, non_spangram
                                ):
                                    solution = Solution(
                                        spangram=ordering,
                                        non_spangram_strands=frozenset(non_spangram),
                                    )
                                    solutions.add(solution)

        # Deduplicate equivalent solutions
        # Compare solutions using __lt__ to ensure consistent choice of which
        # equivalent solution to keep
        unique: dict[tuple, Solution] = {}
        for solution in solutions:
            if solution.key not in unique or solution < unique[solution.key]:
                unique[solution.key] = solution

        return set(unique.values())

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
