from pathlib import Path


def load_dictionary():
    """Loads the ENABLE1 dictionary from the internet."""

    # Define the data directory and file path
    dict_file = (
        Path(__file__).parent.parent.parent / "data" / "dictionary" / "enable1.txt"
    )

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
