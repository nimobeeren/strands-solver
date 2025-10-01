from finder import Finder


def test_find_words():
    grid = [
        ["W", "O", "R", "D"],
        ["T", "E", "S", "T"],
        ["C", "O", "O", "L"],
        ["E", "A", "S", "Y"],
    ]
    finder = Finder(grid)
    words = finder.find_words(current_pos=(0, 0))
    words_str = {w.string for w in words}
    assert words_str == {
        "WOST",
        "WORD",
        "WEST",
        "WORE",
        "WOES",
        "WORT",
        "WORDS",
        "WORTS",
        "WERT",
        "WORSET",
        "WORST",
        "WORSE",
    }


def test_find_words_no_min_length():
    grid = [
        ["W", "O", "R", "D"],
        ["T", "E", "S", "T"],
        ["C", "O", "O", "L"],
        ["E", "A", "S", "Y"],
    ]
    finder = Finder(grid)
    words = finder.find_words(current_pos=(0, 0), min_length=0)
    words_str = {w.string for w in words}
    assert words_str == {
        "WORDS",
        "WE",
        "WORST",
        "WORSE",
        "WORE",
        "WORTS",
        "WOT",
        "WET",
        "WERT",
        "WOE",
        "WOES",
        "WOS",
        "WORT",
        "WEST",
        "WORSET",
        "WOST",
        "WO",
        "WORD",
    }


def test_find_all_words():
    grid = [
        ["W", "O", "R", "D"],
        ["T", "E", "S", "T"],
        ["C", "O", "O", "L"],
        ["E", "A", "S", "Y"],
    ]
    finder = Finder(grid)
    words = finder.find_all_words()
    words_str = {w.string for w in words}
    # fmt: off
    assert words_str == {'CESTOS', 'WORSET', 'TOOTERS', 'ERST', 'ROTES', 'SORE', 'SOWER', 'CEROS', 'TOST', 'STOA', 'SOOTS', 'SLOT', 'ACTOR', 'COOTS', 'WORDS', 'LOOTER', 'EROS', 'TORSO', 'LOOSER', 'WORE', 'SLOE', 'TORSE', 'COSY', 'RECTOS', 'LOSER', 'DREST', 'COOER', 'TOOL', 'TROT', 'COOLS', 'WORST', 'COOT', 'TORES', 'SORT', 'LOOT', 'STOAE', 'STREW', 'TOOLS', 'COST', 'STOAS', 'RECTO', 'DREW', 'STROW', 'TOOT', 'ROTE', 'OOTS', 'LOTS', 'OWES', 'REST', 'TORS', 'WERT', 'TROW', 'SOOT', 'ACES', 'TOOTS', 'TOEA', 'LOOTERS', 'ORTS', 'TRET', 'TORSOS', 'WORT', 'COOLY', 'TOWERS', 'WORTS', 'ORES', 'ROTO', 'TOWER', 'CERO', 'EASY', 'SECTOR', 'TORTS', 'COOS', 'LOST', 'COSET', 'ROES', 'WOST', 'LOOSE', 'SLOTS', 'TWOS', 'WEST', 'SOTS', 'COOERS', 'ROSE', 'SECT', 'TOES', 'TEST', 'RETOOLS', 'WORSE', 'TORT', 'TOOTER', 'LOOS', 'WORD', 'SORD', 'OCAS', 'SEROW', 'COSTLY', 'LOSE', 'RESOW', 'SOYS', 'ROSET', 'TOYS', 'RETOOL', 'ROTOS', 'COOL', 'SOLS', 'WOES', 'SLOES', 'COTES', 'COTE', 'ACTORS', 'TORE'}
    # fmt: on
