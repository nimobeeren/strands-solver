import asyncio
import logging
from typing import Annotated

import typer

from ..dictionary import load_dictionary
from ..embedder import CachePolicy, Embedder

logger = logging.getLogger(__name__)


async def async_embed(reload: bool) -> None:
    logger.info("Loading dictionary...")
    all_words = load_dictionary()
    logger.info(f"Dictionary contains {len(all_words)} words")

    embedder = Embedder()
    try:
        if reload:
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


def embed(
    reload: Annotated[
        bool,
        typer.Option("--reload", help="Re-embed all words, even if already cached."),
    ] = False,
) -> None:
    """Embed dictionary words and store in cache."""
    asyncio.run(async_embed(reload))
