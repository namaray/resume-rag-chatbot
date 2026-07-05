"""
FAISS vector store — manages the index for storing and
searching document embeddings with similarity scoring.
"""

import os
import json
import numpy as np

try:
    import faiss
except ImportError:
    raise ImportError("faiss-cpu is required. Install with: pip install faiss-cpu")

from app.chunker import Chunk


class VectorStore:
    """FAISS-backed vector store with chunk metadata."""

    def __init__(self):
        self.index: faiss.IndexFlatIP | None = None
        self.chunks: list[Chunk] = []
        self.dimension: int = 0

    @property
    def is_loaded(self) -> bool:
        return self.index is not None and len(self.chunks) > 0

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def build_index(self, embeddings: np.ndarray, chunks: list[Chunk]) -> None:
        """
        Build a FAISS index from pre-computed embeddings and their
        corresponding chunks.

        Args:
            embeddings: np.ndarray of shape (n, dim), L2-normalized.
            chunks: List of Chunk objects matching the embeddings.
        """
        if len(embeddings) != len(chunks):
            raise ValueError(
                f"Mismatch: {len(embeddings)} embeddings vs {len(chunks)} chunks"
            )

        self.dimension = embeddings.shape[1]
        self.chunks = chunks

        # IndexFlatIP = inner product; with normalized vectors this equals cosine similarity
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings.astype(np.float32))

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.3,
    ) -> list[dict]:
        """
        Search the index for the most similar chunks to the query.

        Args:
            query_embedding: np.ndarray of shape (1, dim), L2-normalized.
            top_k: Number of results to return.
            threshold: Minimum similarity score to include.

        Returns:
            List of dicts with keys: chunk, score
        """
        if not self.is_loaded:
            raise RuntimeError("Vector store not loaded. Call build_index() or load() first.")

        scores, indices = self.index.search(
            query_embedding.astype(np.float32), top_k
        )

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            if score < threshold:
                continue
            results.append({
                "chunk": self.chunks[idx],
                "score": float(score),
            })

        return results

    def save(self, index_dir: str) -> None:
        """Save the FAISS index and chunk metadata to disk."""
        if not self.is_loaded:
            raise RuntimeError("No index to save.")

        os.makedirs(index_dir, exist_ok=True)

        # Save FAISS index
        index_path = os.path.join(index_dir, "faiss.index")
        faiss.write_index(self.index, index_path)

        # Save chunk metadata as JSON
        chunks_path = os.path.join(index_dir, "chunks.json")
        chunks_data = [c.to_dict() for c in self.chunks]
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)

        print(f"  [OK] Saved index ({self.index.ntotal} vectors) to {index_dir}")

    def load(self, index_dir: str) -> None:
        """Load the FAISS index and chunk metadata from disk."""
        index_path = os.path.join(index_dir, "faiss.index")
        chunks_path = os.path.join(index_dir, "chunks.json")

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index not found: {index_path}")
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Chunks metadata not found: {chunks_path}")

        # Load FAISS index
        self.index = faiss.read_index(index_path)
        self.dimension = self.index.d

        # Load chunk metadata
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)
        self.chunks = [Chunk.from_dict(c) for c in chunks_data]

        if self.index.ntotal != len(self.chunks):
            raise ValueError(
                f"Index has {self.index.ntotal} vectors but "
                f"{len(self.chunks)} chunk records"
            )

        print(f"  [OK] Loaded index ({self.index.ntotal} vectors, dim={self.dimension})")
