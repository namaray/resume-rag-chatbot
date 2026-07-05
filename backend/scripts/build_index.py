"""
Offline index builder — reads documents, chunks them, embeds them,
and saves the FAISS index to disk.

Usage:
    cd backend
    python -m scripts.build_index
"""

import os
import sys
import time

# Force UTF-8 output on Windows to avoid UnicodeEncodeError
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add the backend directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load .env before importing app modules that read settings
load_dotenv()

from app.config import get_settings
from app.chunker import load_and_chunk_documents
from app.embeddings import embed_texts
from app.vector_store import VectorStore


def main():
    settings = get_settings()

    # Resolve paths relative to the backend directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, settings.documents_dir)
    index_dir = os.path.join(base_dir, settings.index_dir)

    print("=" * 60)
    print("  Resume RAG Chatbot -- Index Builder")
    print("=" * 60)

    # -- Validate API key --
    if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
        print("\n[X] ERROR: GEMINI_API_KEY is not set.")
        print("  1. Get a free key from https://aistudio.google.com/")
        print("  2. Copy .env.example to .env")
        print("  3. Paste your key in the GEMINI_API_KEY field")
        sys.exit(1)

    # -- Step 1: Load and chunk documents --
    print(f"\n[1] Loading documents from: {docs_dir}")
    try:
        chunks = load_and_chunk_documents(
            docs_dir,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"[X] ERROR: {e}")
        sys.exit(1)

    print(f"  [OK] Loaded {len(chunks)} chunks from documents")

    # Show sample chunks
    print("\n[*] Sample chunks:")
    for i, chunk in enumerate(chunks[:3]):
        preview = chunk.text[:100].replace("\n", " ")
        print(f"  [{i}] {chunk.source_file} -> \"{preview}...\"")
    if len(chunks) > 3:
        print(f"  ... and {len(chunks) - 3} more")

    # -- Step 2: Generate embeddings --
    print(f"\n[2] Generating embeddings with {settings.gemini_embedding_model}...")
    texts = [c.text for c in chunks]

    start = time.time()
    try:
        embeddings = embed_texts(texts)
    except Exception as e:
        print(f"[X] ERROR generating embeddings: {e}")
        sys.exit(1)
    elapsed = time.time() - start

    print(f"  [OK] Generated {embeddings.shape[0]} embeddings (dim={embeddings.shape[1]}) in {elapsed:.1f}s")

    # -- Step 3: Build and save FAISS index --
    print(f"\n[3] Building FAISS index...")
    store = VectorStore()
    store.build_index(embeddings, chunks)
    store.save(index_dir)

    # -- Step 4: Verify by running a test query --
    print(f"\n[4] Running test query: 'What is Pangochain?'")
    from app.embeddings import embed_query

    test_embedding = embed_query("What is Pangochain?")
    results = store.search(test_embedding, top_k=3)

    for i, r in enumerate(results):
        preview = r["chunk"].text[:80].replace("\n", " ")
        print(f"  [{i+1}] score={r['score']:.3f} | {r['chunk'].source_file} -> \"{preview}...\"")

    # -- Done --
    print("\n" + "=" * 60)
    print("  [OK] Index built successfully!")
    print(f"  Chunks: {len(chunks)}")
    print(f"  Dimension: {embeddings.shape[1]}")
    print(f"  Index saved to: {index_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
