# Strands Solver

A solver for Strands, the New York Times puzzle game.

## Installation

1. Install the [uv](https://docs.astral.sh/uv/) package manager.

2. Download the required NLTK data:

```bash
uv run -m nltk.downloader wordnet words
```

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

- The wordlist (`words.py`) is missing some fairly common words (e.g. LOVERS, OPPOSITES, ZIPLINE, ZIPLINING) and contains many non-existant words. This may cause the solver to fail to find a valid solution or to find an invalid solution.
- The solver will not find the correct solution if the spangram consists of multiple concatenated words (which is often the case). It can only find a solution if the spangram is a single word or if it consists of words which are 4 letters or longer (which it will find as separate words).
