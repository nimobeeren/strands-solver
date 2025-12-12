# Strands Solver

A solver for Strands, the New York Times puzzle game.

## Usage

> [!NOTE]
> To run these examples you need the [uv](https://docs.astral.sh/uv/) package manager.

```bash
uv run strands-solver today  # solve today's puzzle
uv run strands-solver YYYY-MM-DD  # solve another day's puzzle
uv run strands-solver path_to_puzzle.json  # solve puzzle from a file
```

## Goal

This program attempts to solve Strands puzzles in one shot, i.e. without a way to iteratively determine whether the chosen words are correct or not.

More precisely, given

- a rectangular grid of letters
- a phrase describing a theme
- a number specifying the number of strands in the solution

the solver attempts to find a set of strands such that

- every letter in the grid is covered exactly once
- every strand is at least 4 letters long
- there is at least one strand (called the _spangram_) which spans the entire grid vertically or horizontally and which explains the theme
- every strand spells out a valid word (though the spangram may be a concatenation of multiple words)
- all strands are somehow related to the theme
- the number of strands matches the given number

where a _strand_ is a sequence of adjacent letters in the grid.

> [!NOTE]
> There may be multiple strands in a solution which span the entire grid, but only one is deemed the spangram.

### Example

This is the puzzle of 2025-10-03:

```
Theme: Who's in charge?

 A     M     E     L     S     S

 N     A     A     F     E     O

 G     E     R     D     I     B

 E     A     D     E     H     S

 O     H     R     C     I     O

 R     T     C     S     V     R

 D     E     P     H     R     S

 I     R     I     E     P     U

Number of words: 7
```

The goal is then to find this solution:

<img alt="The same grid of letters as earlier, with the word LEADERSHIP highlighted in yellow and the words BOSS, CHIEF, DIRECTOR, MANAGE, SUPERVISOR and HEARD highlighted in blue." src="./assets/example_solution.png" width="300" />

where the strands are

```
🟡 LEADERSHIP (spangram)
🔵 BOSS
🔵 CHIEF
🔵 DIRECTOR
🔵 MANAGER
🔵 SUPERVISOR
🔵 HEAD
```

This is the "correct" solution as provided by the New York Times. There are other valid solutions, but not all match the theme.

## Limitations

- Some puzzles take a very long time to solve (see [notes.md](./puzzles/notes.md)).
- The solver usually finds multiple solutions but it can't determine which one fits the theme best.
- The solver will only find a solution if the spangram is a single word or a concatenation of words which are each 4 letters or longer. In reality, the words in the spangram may be shorter than 4 letters.
- The solver will not find solutions where the spangram contains a contraction (like YOURE), which does appear in real solutions.
- The dictionary (`dictionary.py`) uses the [ENABLE1](https://rressler.quarto.pub/i_data_sets/data_word_lists.html) word list, which is comprehensive but may occasionally miss some valid words or include uncommon ones. This may cause the solver to fail to find a valid solution.

## Development

### Tests

```bash
uv run pytest
```

### Type checking

```bash
uv run pyright
```

### Formatting

```bash
uv run ruff format
```
