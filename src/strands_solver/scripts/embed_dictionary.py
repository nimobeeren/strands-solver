#!/usr/bin/env python3
"""Embeds all words from the dictionary and stores them in the cache."""

import argparse
import logging
import random

from dotenv import load_dotenv

from strands_solver.dictionary import load_dictionary
from strands_solver.embedder import BATCH_SIZE, Embedder

load_dotenv()

# TODO: Remove before committing
TEST_MODE = True

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def get_cached_words(embedder: Embedder) -> set[str]:
    """Returns the set of words already in the cache."""
    cursor = embedder.conn.execute("SELECT content FROM embeddings")
    return {row[0] for row in cursor.fetchall()}


def embed_words(words: list[str], embedder: Embedder) -> None:
    """Embeds words and stores them in the cache."""
    total = len(words)
    for i in range(0, total, BATCH_SIZE):
        batch = words[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} words)")

        embeddings = embedder.get_embeddings(batch, cached=False)
        embedder.store_embeddings(embeddings)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed dictionary words and store in cache."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-embed all words, even if already cached.",
    )
    args = parser.parse_args()

    logger.info("Loading dictionary...")
    all_words = load_dictionary()
    logger.info(f"Dictionary contains {len(all_words)} words")

    # TODO: Remove before committing
    if TEST_MODE:
        random.seed(42)
        all_words = set(random.sample(sorted(all_words), min(1000, len(all_words))))
        logger.info(f"TEST_MODE: Using random sample of {len(all_words)} words")

    embedder = Embedder()
    try:
        if args.force:
            words_to_embed = all_words
            logger.info(f"Force mode: will embed all {len(words_to_embed)} words")
        else:
            cached_words = get_cached_words(embedder)
            words_to_embed = all_words - cached_words
            logger.info(
                f"Found {len(cached_words)} cached words, "
                f"{len(words_to_embed)} words to embed"
            )

        if not words_to_embed:
            logger.info("Nothing to embed, all words are already cached.")
            return

        embed_words(list(words_to_embed), embedder)
        logger.info(f"Done! Embedded {len(words_to_embed)} words.")
    finally:
        embedder.close()


if __name__ == "__main__":
    main()
