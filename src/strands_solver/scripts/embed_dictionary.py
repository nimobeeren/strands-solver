#!/usr/bin/env python3
"""Embeds all words from the dictionary and stores them in the cache."""

import argparse
import asyncio
import logging

from dotenv import load_dotenv

from strands_solver.dictionary import load_dictionary
from strands_solver.embedder import Embedder

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_cached_words(embedder: Embedder) -> set[str]:
    """Returns the set of words already in the cache."""
    cursor = embedder._db_conn.execute("SELECT content FROM embeddings")
    return {row[0] for row in cursor.fetchall()}


async def embed_words(words: list[str], embedder: Embedder) -> None:
    """Embeds words and stores them in the cache."""
    logger.info(f"Embedding {len(words)} words...")
    await embedder.get_embeddings(words, cached=False, store=True)


async def main() -> None:
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

        await embed_words(list(words_to_embed), embedder)
        logger.info(f"Done! Embedded {len(words_to_embed)} words.")
    finally:
        embedder.close()


if __name__ == "__main__":
    asyncio.run(main())
