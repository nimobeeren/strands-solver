import asyncio
import logging
import sqlite3
import struct
from pathlib import Path
from typing import Sequence, cast

import sqlite_vec
from google import genai
from google.genai.types import ContentListUnion, EmbedContentConfig
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


BATCH_SIZE = 100  # Gemini Embedding API limit
MAX_CONCURRENT_REQUESTS = 20
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "embeddings.db"


class Embedder:
    """Text embedding with SQLite-backed caching."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.client = genai.Client().aio
        self.conn = sqlite3.connect(db_path)
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)
        self._init_db()
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    def _init_db(self) -> None:
        """Create tables."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                content TEXT PRIMARY KEY,
                vector BLOB
            )
        """)
        self.conn.commit()

    async def _embed_batch(self, batch: Sequence[str]) -> list[list[float]]:
        @retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=1, min=4, max=60),
            retry=retry_if_exception_type(Exception),
            before_sleep=lambda retry_state: logger.warning(
                f"Rate limited or error: {retry_state.outcome.exception() if retry_state.outcome else 'unknown'}. "
                f"Retrying in {retry_state.next_action.sleep if retry_state.next_action else 0:.1f}s "  # type: ignore[union-attr]
                f"(attempt {retry_state.attempt_number}/5)..."
            ),
        )
        async def _call_api() -> list[list[float]]:
            response = await self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=cast(ContentListUnion, batch),
                config=EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
            )
            assert response.embeddings
            result = []
            for emb in response.embeddings:
                assert emb.values
                result.append(list(emb.values))
            return result

        async with self._semaphore:
            return await _call_api()

    async def get_embeddings(
        self, contents: Sequence[str], cached: bool = True
    ) -> dict[str, list[float]]:
        """Gets embeddings for a list of contents.

        Args:
            contents: The contents to get embeddings for.
            cached: If True, reads from cache and raises KeyError if missing.
                If False, fetches from the API.
        """
        if cached:
            result = {}
            for content in contents:
                row = self.conn.execute(
                    "SELECT vector FROM embeddings WHERE content = ?", (content,)
                ).fetchone()
                if row is None:
                    raise KeyError(f"Embedding not found in cache: {content!r}")
                blob: bytes = row[0]
                num_floats = len(blob) // 4
                result[content] = list(struct.unpack(f"{num_floats}f", blob))
            return result
        else:
            batches = [
                contents[i : i + BATCH_SIZE]
                for i in range(0, len(contents), BATCH_SIZE)
            ]
            total_batches = len(batches)
            completed = 0

            async def embed_with_progress(batch: Sequence[str]) -> list[list[float]]:
                nonlocal completed
                result = await self._embed_batch(batch)
                completed += 1
                logger.info(f"Embedded {completed}/{total_batches} batches")
                return result

            batch_results = await asyncio.gather(
                *[embed_with_progress(batch) for batch in batches]
            )

            result = {}
            for batch, embeddings in zip(batches, batch_results):
                for content, emb in zip(batch, embeddings):
                    result[content] = emb
            return result

    def store_embeddings(self, embeddings: dict[str, list[float]]) -> None:
        """Store embeddings in SQLite."""
        for content, vector in embeddings.items():
            blob = sqlite_vec.serialize_float32(vector)
            self.conn.execute(
                "INSERT OR REPLACE INTO embeddings (content, vector) VALUES (?, ?)",
                (content, blob),
            )
        self.conn.commit()

    def close(self) -> None:
        """Close DB connection."""
        self.conn.close()
