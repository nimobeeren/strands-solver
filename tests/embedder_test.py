from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from strands_solver.embedder import (
    CachePolicy,
    EmbeddingNotFoundError,
    Embedder,
)


@pytest.fixture
def embedder(tmp_path):
    """Embedder with temp SQLite DB."""
    db_path = tmp_path / "test_embeddings.db"
    emb = Embedder(db_path=db_path)
    yield emb
    emb.close()


@pytest.fixture
def api_embeddings():
    """Mutable dict that controls what the mocked API returns."""
    return {}


@pytest.fixture(autouse=True)
def mock_gemini_api(api_embeddings, monkeypatch):
    """Always mock the Gemini API. Set api_embeddings dict to control return values."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    async def mock_embed_content(model, contents, config):
        response = MagicMock()
        response.embeddings = []
        for content in contents:
            if content not in api_embeddings:
                raise ValueError(f"Unexpected API call for content: {content!r}")
            emb = MagicMock()
            emb.values = api_embeddings[content].tolist()
            response.embeddings.append(emb)
        return response

    mock_client = MagicMock()
    mock_client.aio.models.embed_content = AsyncMock(side_effect=mock_embed_content)

    with patch("strands_solver.embedder.genai.Client", return_value=mock_client):
        yield mock_client


@pytest.mark.asyncio
async def test_get_embeddings_default_cache_hit(embedder):
    """DEFAULT with cache hit: returns cached embeddings, no API call."""
    embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    embedder.store_embeddings({"hello": embedding, "world": embedding * 2})

    result = await embedder.get_embeddings(
        ["hello", "world"], cache_policy=CachePolicy.DEFAULT
    )

    assert result["hello"] == pytest.approx(embedding, rel=1e-5)
    assert result["world"] == pytest.approx(embedding * 2, rel=1e-5)


@pytest.mark.asyncio
async def test_get_embeddings_default_cache_miss(embedder, api_embeddings):
    """DEFAULT with cache miss: fetches from API, stores in cache."""
    embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    api_embeddings["hello"] = embedding
    api_embeddings["world"] = embedding * 2

    result = await embedder.get_embeddings(
        ["hello", "world"], cache_policy=CachePolicy.DEFAULT
    )

    assert result["hello"] == pytest.approx(embedding, rel=1e-5)
    assert result["world"] == pytest.approx(embedding * 2, rel=1e-5)

    cached = await embedder.get_embeddings(
        ["hello", "world"], cache_policy=CachePolicy.ONLY_IF_CACHED
    )
    assert cached["hello"] == pytest.approx(embedding, rel=1e-5)
    assert cached["world"] == pytest.approx(embedding * 2, rel=1e-5)


@pytest.mark.asyncio
async def test_get_embeddings_default_partial_cache_hit(embedder, api_embeddings):
    """DEFAULT with partial cache hit: returns cached, fetches missing from API, stores fetched."""
    cached_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    api_embedding = np.array([0.4, 0.5, 0.6], dtype=np.float32)

    embedder.store_embeddings({"cached_content": cached_embedding})
    api_embeddings["uncached_content"] = api_embedding

    result = await embedder.get_embeddings(
        ["cached_content", "uncached_content"], cache_policy=CachePolicy.DEFAULT
    )

    assert result["cached_content"] == pytest.approx(cached_embedding, rel=1e-5)
    assert result["uncached_content"] == pytest.approx(api_embedding, rel=1e-5)

    cached = await embedder.get_embeddings(
        ["uncached_content"], cache_policy=CachePolicy.ONLY_IF_CACHED
    )
    assert cached["uncached_content"] == pytest.approx(api_embedding, rel=1e-5)


@pytest.mark.asyncio
async def test_get_embeddings_reload(embedder, api_embeddings):
    """RELOAD: skips cache, fetches from API, overwrites cache with new value."""
    old_embedding = np.array([0.1, 0.1, 0.1], dtype=np.float32)
    new_embedding = np.array([0.9, 0.9, 0.9], dtype=np.float32)

    embedder.store_embeddings({"content": old_embedding})
    api_embeddings["content"] = new_embedding

    result = await embedder.get_embeddings(["content"], cache_policy=CachePolicy.RELOAD)

    assert result["content"] == pytest.approx(new_embedding, rel=1e-5)

    cached = await embedder.get_embeddings(
        ["content"], cache_policy=CachePolicy.ONLY_IF_CACHED
    )
    assert cached["content"] == pytest.approx(new_embedding, rel=1e-5)


@pytest.mark.asyncio
async def test_get_embeddings_no_store(embedder, api_embeddings):
    """NO_STORE: skips cache read, fetches from API, does not store in cache."""
    embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    api_embeddings["content"] = embedding

    result = await embedder.get_embeddings(
        ["content"], cache_policy=CachePolicy.NO_STORE
    )

    assert result["content"] == pytest.approx(embedding, rel=1e-5)

    with pytest.raises(EmbeddingNotFoundError):
        await embedder.get_embeddings(
            ["content"], cache_policy=CachePolicy.ONLY_IF_CACHED
        )


@pytest.mark.asyncio
async def test_get_embeddings_only_if_cached_cache_hit(embedder):
    """ONLY_IF_CACHED with cache hit: returns cached embedding, no API call."""
    embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    embedder.store_embeddings({"content": embedding})

    result = await embedder.get_embeddings(
        ["content"], cache_policy=CachePolicy.ONLY_IF_CACHED
    )

    assert result["content"] == pytest.approx(embedding, rel=1e-5)


@pytest.mark.asyncio
async def test_get_embeddings_only_if_cached_cache_miss(embedder):
    """ONLY_IF_CACHED with cache miss: raises EmbeddingNotFoundError."""
    with pytest.raises(EmbeddingNotFoundError, match="nonexistent"):
        await embedder.get_embeddings(
            ["nonexistent"], cache_policy=CachePolicy.ONLY_IF_CACHED
        )


def test_get_cached_contents_empty(embedder):
    """Returns empty set when cache is empty."""
    assert embedder.get_cached_contents() == set()


def test_get_cached_contents_returns_all_cached(embedder):
    """Returns all cached content strings (words, themes, etc.)."""
    embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    embedder.store_embeddings(
        {
            "word1": embedding,
            "word2": embedding,
            "theme: animals": embedding,
        }
    )

    cached = embedder.get_cached_contents()

    assert cached == {"word1", "word2", "theme: animals"}


@pytest.mark.asyncio
async def test_store_embeddings_overwrites_existing(embedder):
    """Storing an embedding for existing content overwrites the old value."""
    old_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    new_embedding = np.array([0.7, 0.8, 0.9], dtype=np.float32)

    embedder.store_embeddings({"content": old_embedding})
    embedder.store_embeddings({"content": new_embedding})

    result = await embedder.get_embeddings(
        ["content"], cache_policy=CachePolicy.ONLY_IF_CACHED
    )

    assert result["content"] == pytest.approx(new_embedding, rel=1e-5)
