from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from strands_solver.embedder import BATCH_SIZE, Embedder


@pytest.fixture
def embedder(tmp_path):
    """Embedder with temp SQLite DB."""
    db_path = tmp_path / "test_embeddings.db"
    with patch("strands_solver.embedder.genai.Client"):
        emb = Embedder(db_path=db_path)
    yield emb
    emb.close()


@pytest.fixture
def mock_embedding():
    """Sample embedding vector."""
    return np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)


@pytest.mark.asyncio
async def test_store_and_retrieve_embeddings(embedder, mock_embedding):
    """Store and retrieve from cache."""
    embeddings = {"hello": mock_embedding, "world": mock_embedding}
    embedder.store_embeddings(embeddings)

    result = await embedder.get_embeddings(["hello", "world"], cached=True)

    assert len(result) == 2
    assert result["hello"] == pytest.approx(mock_embedding, rel=1e-5)
    assert result["world"] == pytest.approx(mock_embedding, rel=1e-5)


@pytest.mark.asyncio
async def test_get_embeddings_cached_raises_on_missing(embedder):
    """cached=True raises KeyError for missing content."""
    with pytest.raises(KeyError, match="not found in cache"):
        await embedder.get_embeddings(["nonexistent"], cached=True)


@pytest.mark.asyncio
async def test_store_embeddings_overwrites_existing(embedder, mock_embedding):
    """Storing overwrites existing."""
    embedder.store_embeddings({"content": np.array([1.0, 2.0, 3.0], dtype=np.float32)})
    embedder.store_embeddings({"content": mock_embedding})

    result = await embedder.get_embeddings(["content"], cached=True)

    assert result["content"] == pytest.approx(mock_embedding, rel=1e-5)


@pytest.mark.asyncio
async def test_get_embeddings_uncached_calls_api(embedder, mock_embedding):
    """cached=False calls Gemini API."""
    mock_response = MagicMock()
    mock_emb = MagicMock()
    mock_emb.values = mock_embedding.tolist()
    mock_response.embeddings = [mock_emb]
    embedder.client.models.embed_content = AsyncMock(return_value=mock_response)

    result = await embedder.get_embeddings(["test"], cached=False)

    assert result["test"] == pytest.approx(mock_embedding, rel=1e-5)
    embedder.client.models.embed_content.assert_called_once()


@pytest.mark.asyncio
async def test_get_embeddings_batches_large_requests(embedder, mock_embedding):
    """Requests >BATCH_SIZE are split."""
    contents = [f"content{i}" for i in range(BATCH_SIZE + 10)]

    def make_response(batch_size):
        resp = MagicMock()
        resp.embeddings = [
            MagicMock(values=mock_embedding.tolist()) for _ in range(batch_size)
        ]
        return resp

    embedder.client.models.embed_content = AsyncMock(
        side_effect=[make_response(BATCH_SIZE), make_response(10)]
    )

    result = await embedder.get_embeddings(contents, cached=False)

    assert len(result) == len(contents)
    assert embedder.client.models.embed_content.call_count == 2
