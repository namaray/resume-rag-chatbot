"""
Gemini embeddings client — wraps the Google GenAI SDK to embed
text chunks and queries using the text-embedding-004 model.
"""

import time
import numpy as np
from google import genai

from app.config import get_settings


# Module-level client (initialized lazily)
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Get or create the Gemini client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def embed_texts(
    texts: list[str],
    batch_size: int = 50,
    max_retries: int = 3,
) -> np.ndarray:
    """
    Embed a list of texts using Gemini's embedding model.
    Processes in batches to respect API limits.

    Returns:
        np.ndarray of shape (len(texts), embedding_dim) with L2-normalized vectors.
    """
    settings = get_settings()
    client = _get_client()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                result = client.models.embed_content(
                    model=settings.gemini_embedding_model,
                    contents=batch,
                )
                # Extract embedding vectors from the response
                batch_embeddings = [e.values for e in result.embeddings]
                all_embeddings.extend(batch_embeddings)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(
                        f"Failed to embed batch {i // batch_size} after "
                        f"{max_retries} retries: {e}"
                    ) from e
                print(
                    f"  ⚠ Embedding attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {retry_delay:.1f}s..."
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

        # Small delay between batches to avoid rate limiting
        if i + batch_size < len(texts):
            time.sleep(0.2)

    embeddings = np.array(all_embeddings, dtype=np.float32)

    # L2 normalize for cosine similarity via inner product
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)  # avoid division by zero
    embeddings = embeddings / norms

    return embeddings


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string.

    Returns:
        np.ndarray of shape (1, embedding_dim) with L2-normalized vector.
    """
    return embed_texts([query])
