from PIL import Image

import ocr


def test_extract_grid():
    image = Image.open("./puzzles/2025-09-14.jpeg")
    result = ocr.extract_grid(image)
    assert result == [
        ["T", "S", "S", "L", "K", "P"],
        ["H", "E", "A", "O", "E", "O"],
        ["S", "Y", "D", "W", "Y", "S"],
        ["N", "I", "G", "G", "U", "L"],
        ["L", "O", "T", "S", "O", "F"],
        ["R", "E", "I", "X", "E", "A"],
        ["E", "U", "S", "A", "D", "S"],
        ["L", "Y", "R", "E", "L", "T"],
    ]


def test_extract_theme():
    image = Image.open("./puzzles/2025-09-14.jpeg")
    result = ocr.extract_theme(image)
    assert result == "Hurry up!"
