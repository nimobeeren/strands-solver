from pathlib import Path


def _get_dictionary_path() -> Path:
    """Returns the path to the dictionary file.

    Checks the development location first (data/dictionary/), then falls back
    to the installed package location (strands_solver/data/).
    """
    # Development location: workspace root / data / dictionary / enable1.txt
    dev_path = Path(__file__).parent.parent.parent / "data" / "dictionary" / "enable1.txt"
    if dev_path.exists():
        return dev_path

    # Installed package location: strands_solver / data / enable1.txt
    pkg_path = Path(__file__).parent / "data" / "enable1.txt"
    if pkg_path.exists():
        return pkg_path

    raise FileNotFoundError(
        f"Dictionary file not found. Checked:\n  - {dev_path}\n  - {pkg_path}"
    )


def load_dictionary():
    """Loads the ENABLE1 dictionary bundled with the package."""
    dict_file = _get_dictionary_path()

    # Read and process the words
    with open(dict_file, "r") as f:
        words = f.readlines()

    # Strip whitespace, convert to uppercase, and filter to only A-Z characters
    words = {
        word.strip().upper()
        for word in words
        if word.strip().isalpha() and word.strip().isascii()
    }

    # Add valid single-letter words
    words |= {"A", "I"}

    # Add single-letter elisions (of -> 'o as in "twelve o' clock"; and -> 'n as in "wait 'n see")
    # Not sure if these ever appear in real solutions
    # words |= {"O", "N"}

    return words
