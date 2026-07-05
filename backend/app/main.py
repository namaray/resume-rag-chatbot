"""
FastAPI application — main entry point.
Serves the /api/chat, /api/health, and /api/suggestions endpoints.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.vector_store import VectorStore
from app.rag import generate_answer
from app.models import ChatRequest, ChatResponse, HealthResponse

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("resume-chatbot")

# ── Shared state ──────────────────────────────────────────────
vector_store = VectorStore()

# ── Rate limiter ──────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── Suggested starter questions ───────────────────────────────
SUGGESTIONS = [
    "What is Pangochain?",
    "What are his main technical skills?",
    "Describe his ML research work.",
    "What work experience does he have?",
    "Tell me about his education.",
]


# ── Lifespan: load index on startup ──────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the FAISS index when the server starts."""
    settings = get_settings()

    # Resolve index directory relative to the backend folder
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_dir = os.path.join(base_dir, settings.index_dir)

    logger.info("Starting Resume RAG Chatbot API")

    if os.path.exists(os.path.join(index_dir, "faiss.index")):
        try:
            vector_store.load(index_dir)
            logger.info(
                f"[OK] Index loaded: {vector_store.chunk_count} chunks, "
                f"dim={vector_store.dimension}"
            )
        except Exception as e:
            logger.error(f"[X] Failed to load index: {e}")
    else:
        logger.warning(
            f"[!] No index found at {index_dir}. "
            "Run `python -m scripts.build_index` to build it."
        )

    yield  # App runs here

    logger.info("Shutting down")


# ── App factory ───────────────────────────────────────────────
app = FastAPI(
    title="Resume RAG Chatbot API",
    description="Ask questions about the resume, projects, and background.",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit(get_settings().rate_limit)
async def chat(request: Request, body: ChatRequest):
    """
    Ask a question about the resume/projects.
    Returns a grounded answer with source citations.
    """
    if not vector_store.is_loaded:
        return ChatResponse(
            answer=(
                "The chatbot is still initializing. "
                "Please try again in a moment."
            ),
            sources=[],
            model_used="",
            response_time_ms=0,
        )

    logger.info(f"Question: {body.question[:80]}...")
    response = generate_answer(body.question, vector_store)
    logger.info(
        f"Answer generated in {response.response_time_ms}ms "
        f"({len(response.sources)} sources)"
    )
    return response


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check — returns index status."""
    settings = get_settings()
    return HealthResponse(
        status="ok" if vector_store.is_loaded else "no_index",
        index_loaded=vector_store.is_loaded,
        chunk_count=vector_store.chunk_count,
        model=settings.gemini_chat_model,
    )


@app.get("/api/suggestions")
async def suggestions():
    """Return suggested starter questions."""
    return {"suggestions": SUGGESTIONS}

# Mount frontend directory for easy local testing
from fastapi.staticfiles import StaticFiles
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
