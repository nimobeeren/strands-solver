import argparse

from ocr import load_grid_from_csv
from solver import Solver


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("grid", type=str)
    args = parser.parse_args()

    grid = load_grid_from_csv(args.grid)

    print("Solving puzzle:")
    for row in grid:
        print(" ".join(row))

    solver = Solver(grid)
    words = solver.find_all_words()
    print(words)
