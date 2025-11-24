import logging
from pathlib import Path

import httpx


def load_dictionary():
    """Loads the ENABLE1 dictionary from the internet."""

    # Define the data directory and file path
    data_dir = Path(__file__).parent.parent.parent / "data"
    dict_file = data_dir / "enable1_words.txt"

    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)

    # Download the dictionary file if it doesn't exist
    if not dict_file.exists():
        url = "https://raw.githubusercontent.com/rressler/data_raw_courses/main/enable1_words.txt"
        logging.info("Downloading dictionary")
        response = httpx.get(url)
        response.raise_for_status()
        dict_file.write_text(response.text)
        logging.info(f"Dictionary saved to {dict_file}")

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
    words |= {"O", "N"}

    return words
