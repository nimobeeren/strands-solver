#!/usr/bin/env python3
"""Embeds all words from the dictionary and stores them in the cache."""

import argparse
import asyncio
import logging

from dotenv import load_dotenv

from strands_solver.dictionary import load_dictionary
from strands_solver.embedder import CachePolicy, Embedder

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed dictionary words and store in cache."
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Re-embed all words, even if already cached.",
    )
    args = parser.parse_args()

    logger.info("Loading dictionary...")
    all_words = load_dictionary()
    logger.info(f"Dictionary contains {len(all_words)} words")

    embedder = Embedder()
    try:
        if args.reload:
            words_to_embed = all_words
            logger.info(f"Reload mode: will embed all {len(words_to_embed)} words")
            await embedder.get_embeddings(
                list(all_words), cache_policy=CachePolicy.RELOAD
            )
        else:
            cached_contents = embedder.get_cached_contents()
            words_to_embed = all_words - cached_contents
            if not words_to_embed:
                logger.info("Nothing to embed, all words are already cached.")
                return
            logger.info(
                f"Found {len(cached_contents)} cached contents, "
                f"{len(words_to_embed)} words to embed"
            )
            await embedder.get_embeddings(list(words_to_embed))

        logger.info(f"Done! Embedded {len(words_to_embed)} words.")
    finally:
        embedder.close()


if __name__ == "__main__":
    asyncio.run(main())
