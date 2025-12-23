import logging
import sqlite3
import struct
from pathlib import Path
from typing import Sequence, cast

import sqlite_vec
from google import genai
from google.genai.types import ContentListUnion, EmbedContentConfig
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


BATCH_SIZE = 250  # Gemini Embedding API limit
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "embeddings.db"


class Embedder:
    """Text embedding with SQLite-backed caching."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.client = genai.Client()
        self.conn = sqlite3.connect(db_path)
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)
        self._init_db()

    def _init_db(self) -> None:
        """Create tables."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                content TEXT PRIMARY KEY,
                vector BLOB
            )
        """)
        self.conn.commit()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(60),
        before_sleep=lambda retry_state: logger.error(
            f"Error: {retry_state.outcome.exception() if retry_state.outcome else 'unknown'}. "
            f"Waiting 60s before retry {retry_state.attempt_number}..."
        ),
    )
    def _embed_batch(self, batch: Sequence[str]) -> list[list[float]]:
        response = self.client.models.embed_content(
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

    def get_embeddings(
        self, contents: Sequence[str], cached: bool = True
    ) -> dict[str, list[float]]:
        """Gets embeddings for a list of contents.
        Args:
            contents: The contents to get embeddings for.
            cached: Whether to use the cache. If True and embeddings are not in the
                cache, raises a KeyError.
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
            result = {}
            for i in range(0, len(contents), BATCH_SIZE):
                batch = contents[i : i + BATCH_SIZE]
                embeddings = self._embed_batch(batch)
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
