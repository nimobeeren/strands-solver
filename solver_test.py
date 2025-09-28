from ocr import load_grid_from_csv
from solver import Solver, Strand


def test_solve():
    grid = load_grid_from_csv("./puzzles/example.csv")
    solver = Solver(grid)
    solution = solver.solve()
    assert solution == [
        Strand(positions=[(0, 0), (1, 0), (2, 0), (3, 0)], string="WORD"),
        Strand(positions=[(0, 1), (1, 1), (2, 1), (3, 1)], string="TEST"),
        Strand(positions=[(0, 2), (1, 2), (2, 2), (3, 2)], string="COOL"),
        Strand(positions=[(0, 3), (1, 3), (2, 3), (3, 3)], string="EASY"),
    ]


def test_find_words_no_min_length():
    grid = load_grid_from_csv("./puzzles/example.csv")
    solver = Solver(grid)
    words = solver.find_words(current_pos=(0, 0), min_length=0)
    words_str = {w.string for w in words}
    assert words_str == {
        "W",
        "WO",
        "WORD",
        "WORDS",
        "WORT",
        "WORST",
        "WORSE",
        "WORSET",
        "WORE",
        "WOE",
        "WOT",
        "WOTE",
        "WE",
        "WES",
        "WEST",
        "WET",
        "WER",
        "WERT",
        "WTO",
        "WTC",
        "WTO",
    }


def test_find_words():
    grid = load_grid_from_csv("./puzzles/example.csv")
    solver = Solver(grid)
    words = solver.find_words(current_pos=(0, 0))
    words_str = {w.string for w in words}
    assert words_str == {
        "WORD",
        "WORDS",
        "WORT",
        "WORST",
        "WORSE",
        "WORSET",
        "WORE",
        "WOTE",
        "WEST",
        "WERT",
    }


def test_find_all_words():
    grid = load_grid_from_csv("./puzzles/example.csv")
    solver = Solver(grid)
    words = solver.find_all_words()
    words_str = {w.string for w in words}
    # fmt: off
    assert words_str == {"WORD", "WORDS", "WORT", "WORST", "WORSE", "WORSET", "WORE", "WOTE", "WEST", "WERT", "TEST", "TECO", "TECA", "TOOL", "TOOT", "TOSY", "TOEA", "TOST", "TORT", "TORSO", "TORSO", "TORSE", "TORE", "TOST", "TOWER", "COOL", "COOLY", "COOS", "COOSA", "COOER", "COOS", "COOST", "COOSER", "COOT", "COSY", "COTE", "COTO", "COST", "COSTLY", "COSET", "CEST", "CERT", "CERO", "EASY", "ORTOL", "OREO", "OREO", "OSLO", "OTOE", "OTOE", "OWER", "ERST", "EROS", "OSLO", "OCTOSE", "OTOE", "OSLO", "ACTOR", "ACER", "AOTES", "REST", "RESLOT", "RESOW", "RECOOL", "RECT", "RECTO", "RECTO", "RETOOL", "ROSE", "ROSET", "ROTE", "ROTO", "ROTC", "ROWET", "STOA", "STOOT", "STRE", "STRET", "STREW", "STROW", "SLOO", "SLOE", "SLOT", "SOSO", "SOOT", "SOOTER", "SOOL", "SOOT", "SOSO", "SOCE", "SOCE", "SOTER", "SECOS", "SECT", "SECTOR", "SERT", "SERO", "SEROW", "SORT", "SORTLY", "SORE", "SOTER", "SOWETO", "SOWER", "SOWT", "SOWTE", "SACO", "SOOL", "SOOT", "SOCE", "SOCE", "SOTER", "SOSO", "SOSO", "SOOT", "SOOTER", "SOSO", "SOSO", "SOTS", "SLOO", "SLOE", "SLOT", "DREST", "DREW", "DROW", "TOSY", "TOOT", "TOOTER", "TOETOE", "TRET", "TROT", "TROW", "LOOS", "LOOT", "LOOTER", "LOOS", "LOOSE", "LOOSER", "LOST", "LOSE", "LOSER", "LOTS"}
    # fmt: on
