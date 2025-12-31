import asyncio
import logging
import os
import sqlite3
from enum import Enum
from pathlib import Path
from typing import Sequence, cast

import numpy as np
import numpy.typing as npt
import sqlite_vec
from google import genai
from google.genai.types import ContentListUnion, EmbedContentConfig
from tenacity import RetryCallState, RetryError, retry

logger = logging.getLogger(__name__)


BATCH_SIZE = 100  # Gemini Embedding API limit
MAX_CONCURRENT_REQUESTS = 10
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "embeddings.db"


class CachePolicy(Enum):
    """Cache policy based on JavaScript Fetch API."""

    DEFAULT = "default"
    """Read cache → generate fallback → store"""
    RELOAD = "reload"
    """Skip read → generate → store"""
    NO_STORE = "no-store"
    """Skip read → generate → skip store"""
    ONLY_IF_CACHED = "only-if-cached"
    """Read cache only → error if miss"""


class EmbeddingNotFoundError(Exception):
    """Raised when a required embedding is not found in the cache."""

    pass


class ApiKeyError(Exception):
    """Raised when the Gemini API key is missing or invalid."""

    pass


class Embedder:
    """Text embedding with SQLite-backed caching."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self._db_conn = sqlite3.connect(db_path)
        self._db_conn.enable_load_extension(True)
        sqlite_vec.load(self._db_conn)
        self._db_conn.enable_load_extension(False)
        self._init_db()
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    def _init_db(self) -> None:
        """Create tables."""
        self._db_conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                content TEXT PRIMARY KEY,
                vector BLOB
            )
        """)
        self._db_conn.commit()

    def _is_rate_limit_error(self, exc: BaseException) -> bool:
        exc_str = str(exc).lower()
        return "429" in exc_str or "rate" in exc_str or "quota" in exc_str

    def _is_client_error(self, exc: BaseException) -> bool:
        """Check if this is a 4xx client error (except rate limiting)."""
        exc_str = str(exc)
        # Match "400", "401", "403", etc. but not "429" (rate limit)
        return any(f"{code}" in exc_str for code in range(400, 429)) or any(
            f"{code}" in exc_str for code in range(430, 500)
        )

    def _should_stop_retry(self, retry_state: RetryCallState) -> bool:
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        if exc and self._is_rate_limit_error(exc):
            return False  # Never stop for rate limit errors
        if exc and self._is_client_error(exc):
            return True  # Don't retry client errors (invalid API key, etc.)
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
        if not os.getenv("GEMINI_API_KEY"):
            raise ApiKeyError("GEMINI_API_KEY environment variable is not set")

        @retry(
            stop=self._should_stop_retry,
            wait=self._get_retry_wait,
            before_sleep=self._log_retry,
        )
        async def _call_api() -> list[npt.NDArray[np.float32]]:
            response = await genai.Client().aio.models.embed_content(
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
            try:
                return await _call_api()
            except RetryError as e:
                # Check underlying cause for API key errors
                cause = e.last_attempt.exception()
                if cause and "API_KEY_INVALID" in str(cause):
                    raise ApiKeyError("GEMINI_API_KEY is invalid") from e
                raise

    def _get_cached(self, content: str) -> npt.NDArray[np.float32] | None:
        """Get a single embedding from cache, or None if not found."""
        row = self._db_conn.execute(
            "SELECT vector FROM embeddings WHERE content = ?", (content,)
        ).fetchone()
        if row is None:
            return None
        blob: bytes = row[0]
        return np.frombuffer(blob, dtype=np.float32).copy()

    async def _generate(
        self, contents: list[str], *, store: bool
    ) -> dict[str, npt.NDArray[np.float32]]:
        """Generate embeddings using API and optionally store them."""
        if not contents:
            return {}

        batches = [
            contents[i : i + BATCH_SIZE] for i in range(0, len(contents), BATCH_SIZE)
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

    async def get_embeddings(
        self,
        contents: Sequence[str],
        cache_policy: CachePolicy = CachePolicy.DEFAULT,
    ) -> dict[str, npt.NDArray[np.float32]]:
        """Get embeddings for a list of contents.

        Args:
            contents: The contents to get embeddings for.
            cache_policy: Controls cache behavior.
        """
        result: dict[str, npt.NDArray[np.float32]] = {}

        match cache_policy:
            case CachePolicy.DEFAULT:
                # Read cache → generate fallback → store
                to_generate: list[str] = []
                for content in contents:
                    cached = self._get_cached(content)
                    if cached is not None:
                        result[content] = cached
                    else:
                        to_generate.append(content)
                generated = await self._generate(to_generate, store=True)
                result.update(generated)
            case CachePolicy.RELOAD:
                # Skip read → generate → store
                generated = await self._generate(list(contents), store=True)
                result.update(generated)
            case CachePolicy.NO_STORE:
                # Skip read → generate → skip store
                generated = await self._generate(list(contents), store=False)
                result.update(generated)
            case CachePolicy.ONLY_IF_CACHED:
                # Read cache only → error if miss
                for content in contents:
                    cached = self._get_cached(content)
                    if cached is None:
                        raise EmbeddingNotFoundError(
                            f"Embedding not found for {content!r}."
                        )
                    result[content] = cached
            case _:
                raise ValueError(f"Invalid cache policy: {cache_policy}")

        return result

    def get_cached_contents(self) -> set[str]:
        """Return the set of all cached content strings."""
        cursor = self._db_conn.execute("SELECT content FROM embeddings")
        return {row[0] for row in cursor.fetchall()}

    def store_embeddings(self, embeddings: dict[str, npt.NDArray[np.float32]]) -> None:
        """Store embeddings in the cache."""
        for content, vector in embeddings.items():
            blob = vector.tobytes()
            self._db_conn.execute(
                "INSERT OR REPLACE INTO embeddings (content, vector) VALUES (?, ?)",
                (content, blob),
            )
        self._db_conn.commit()

    def close(self) -> None:
        """Close DB connection."""
        self._db_conn.close()
