# Strands Solver

A solver for Strands, the New York Times puzzle game.

## Installation

Install the [uv](https://docs.astral.sh/uv/) package manager.

The dictionary will be automatically downloaded on first use.

## Usage

1. Take a screenshot of the puzzle.

2. Recognize the characters of the puzzle grid and save them to a CSV file:

```bash
uv run ocr.py path_to_puzzle.jpeg path_to_puzzle.csv
```

Note: the defaults are tuned for iPhone 15 screenshots; for other devices, you may need to adjust parameters. Run `uv run ocr.py --help` for more information.

3. Run the solver:

```bash
uv run main.py path_to_puzzle.csv
```

## Limitations

- The dictionary (`dictionary.py`) uses the [ENABLE1](https://rressler.quarto.pub/i_data_sets/data_word_lists.html) word list, which is comprehensive but may occasionally miss some valid words or include uncommon ones. This may cause the solver to fail to find a valid solution.
- The solver will not find the correct solution if the spangram consists of multiple concatenated words (which is often the case). It can only find a solution if the spangram is a single word or if it consists of words which are 4 letters or longer (which it will find as separate words).

## Development

### Tests

Run the tests

```bash
uv run pytest
```

The `ocr_test.py` is a bit slow so you if you don't need it you can skip it with `--ignore ocr_test.py`
