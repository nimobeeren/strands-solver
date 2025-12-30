import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Sequence, cast

import numpy as np
import numpy.typing as npt
import sqlite_vec
from google import genai
from google.genai.types import ContentListUnion, EmbedContentConfig
from tenacity import RetryCallState, retry

logger = logging.getLogger(__name__)


BATCH_SIZE = 100  # Gemini Embedding API limit
MAX_CONCURRENT_REQUESTS = 10
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

    def can_get_embeddings(self, cached: bool) -> bool:
        """Check if embeddings can be retrieved.

        Args:
            cached: If True, checks if the database contains all dictionary words.
                If False, always returns True (API is assumed available).
        """
        if not cached:
            return True

        try:
            from .dictionary import load_dictionary

            dictionary = list(load_dictionary())

            # Check if all dictionary words appear in the database (batched)
            batch_size = 1000
            found_count = 0
            for i in range(0, len(dictionary), batch_size):
                batch = dictionary[i : i + batch_size]
                placeholders = ",".join("?" * len(batch))
                cursor = self.conn.execute(
                    f"SELECT COUNT(*) FROM embeddings WHERE content IN ({placeholders})",
                    batch,
                )
                found_count += cursor.fetchone()[0]

            return found_count >= len(dictionary)
        except Exception:
            logger.exception(
                "Exception occurred while checking embeddings availability, "
                "assuming embeddings are not available."
            )
            return False

    def _is_rate_limit_error(self, exc: BaseException) -> bool:
        exc_str = str(exc).lower()
        return "429" in exc_str or "rate" in exc_str or "quota" in exc_str

    def _should_stop_retry(self, retry_state: RetryCallState) -> bool:
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        if exc and self._is_rate_limit_error(exc):
            return False  # Never stop for rate limit errors
        return retry_state.attempt_number >= 5

    def _get_retry_wait(self, retry_state: RetryCallState) -> float:
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        if exc and self._is_rate_limit_error(exc):
            return 60
        # Fast exponential backoff: 1s, 2s, 4s, 8s, ...
        return min(2 ** (retry_state.attempt_number - 1), 30)

    def _log_retry(self, retry_state: RetryCallState) -> None:
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        wait_time = retry_state.next_action.sleep if retry_state.next_action else 0
        attempt = retry_state.attempt_number

        if exc and self._is_rate_limit_error(exc):
            logger.info(
                f"Rate limited. Retrying in {wait_time:.0f}s (attempt {attempt})..."
            )
        else:
            logger.error(
                f"Error: {exc}. Retrying in {wait_time:.0f}s (attempt {attempt}/5)..."
            )

    async def _embed_batch(self, batch: Sequence[str]) -> list[npt.NDArray[np.float32]]:
        @retry(
            stop=self._should_stop_retry,
            wait=self._get_retry_wait,
            before_sleep=self._log_retry,
        )
        async def _call_api() -> list[npt.NDArray[np.float32]]:
            response = await self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=cast(ContentListUnion, batch),
                config=EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
            )
            assert response.embeddings
            result = []
            for emb in response.embeddings:
                assert emb.values
                result.append(np.asarray(emb.values, dtype=np.float32))
            return result

        async with self._semaphore:
            return await _call_api()

    async def get_embeddings(
        self, contents: Sequence[str], cached: bool = True, store: bool = False
    ) -> dict[str, npt.NDArray[np.float32]]:
        """Gets embeddings for a list of contents. Returns a dictionary mapping each
        content element to its embedding.

        Args:
            contents: The contents to get embeddings for.
            cached: Whether to read from cache or fetch from an API.
            store: Whether to store any embeddings that were fetched from an API in
                the cache.
        """
        if cached:
            if store:
                logger.warning("store=True has no effect when cached=True")
            result: dict[str, npt.NDArray[np.float32]] = {}
            for content in contents:
                row = self.conn.execute(
                    "SELECT vector FROM embeddings WHERE content = ?", (content,)
                ).fetchone()
                if row is None:
                    raise KeyError(f"Content not found in cache: {content!r}")
                blob: bytes = row[0]
                result[content] = np.frombuffer(blob, dtype=np.float32).copy()
            return result
        else:
            batches = [
                contents[i : i + BATCH_SIZE]
                for i in range(0, len(contents), BATCH_SIZE)
            ]
            total_batches = len(batches)
            completed = 0

            async def embed_with_progress(
                batch: Sequence[str],
            ) -> dict[str, npt.NDArray[np.float32]]:
                nonlocal completed
                embeddings = await self._embed_batch(batch)
                batch_result = dict(zip(batch, embeddings))
                if store:
                    self.store_embeddings(batch_result)
                completed += 1
                logger.info(f"Embedded {completed}/{total_batches} batches")
                return batch_result

            batch_results = await asyncio.gather(
                *[embed_with_progress(batch) for batch in batches]
            )

            combined: dict[str, npt.NDArray[np.float32]] = {}
            for batch_result in batch_results:
                combined.update(batch_result)
            return combined

    def store_embeddings(self, embeddings: dict[str, npt.NDArray[np.float32]]) -> None:
        """Store embeddings in the cache."""
        for content, vector in embeddings.items():
            blob = vector.tobytes()
            self.conn.execute(
                "INSERT OR REPLACE INTO embeddings (content, vector) VALUES (?, ?)",
                (content, blob),
            )
        self.conn.commit()

    def close(self) -> None:
        """Close DB connection."""
        self.conn.close()
