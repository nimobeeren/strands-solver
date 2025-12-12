# Strands Solver

A solver for Strands, the New York Times puzzle game.

## Goal

This program attempts to solve Strands puzzles in one shot, i.e. without a way to iteratively determine whether the chosen words are correct or not.

More precisely, given

- a rectangular grid of letters
- a phrase describing a theme
- a number specifying the number of strands in the solution

the solver attempts to find a set of strands such that

- every letter in the grid is covered exactly once
- every strand spells out a valid word
- there is at least one strand (called the _spangram_) which spans the entire grid vertically or horizontally
- the words are somehow related to the theme
- the number of strands matches the requirement

where a _strand_ is a sequence of adjacent letters in the grid.

Note: the spangram can also be a concatenation of multiple words, but other strands cannot. There can however be multiple strands in a solution which span the entire grid.

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

The solution of this puzzle can be visualized as:

![The same grid of letters as earlier, with the word LEADERSHIP highlighted in yellow and the words BOSS, CHIEF, DIRECTOR, MANAGE, SUPERVISOR and HEARD highlighted in blue.](./assets/example_solution.png)

where the strands are

```
🟡 LEADERSHIP (spangram)
🔵 BOSS
🔵 CHIEF
🔵 DIRECTOR
🔵 MANAGE
🔵 SUPERVISOR
🔵 HEARD
```

Actually, the correct solution has HEAD instead of HEARD and MANAGER instead of MANAGE, but we'll ignore that for now 🤫

## Prerequisites

Install the [uv](https://docs.astral.sh/uv/) package manager.

The dictionary will be automatically downloaded on first use.

## Usage

To solve today's puzzle:

```bash
uv run strands-solver today
```

To solve a puzzle from a given date:

```bash
uv run strands-solver 2025-11-30
```

To solve a puzzle from a JSON file:

```bash
uv run strands-solver path_to_puzzle.json
```

See `puzzles/` for the expected structure of the puzzle JSON file.

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
