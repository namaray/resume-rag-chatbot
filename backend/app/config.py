"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """All app settings, loaded from .env file or environment variables."""

    # ── Required ──────────────────────────────────────────────
    gemini_api_key: str = ""

    # ── Gemini Models ─────────────────────────────────────────
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"

    # ── CORS ──────────────────────────────────────────────────
    cors_origins: str = "*"

    # ── Rate Limiting ─────────────────────────────────────────
    rate_limit: str = "10/minute"

    # ── Retrieval Settings ────────────────────────────────────
    top_k: int = 5
    similarity_threshold: float = 0.3

    # ── Paths ─────────────────────────────────────────────────
    documents_dir: str = "data/documents"
    index_dir: str = "data/index"

    # ── Chunking ──────────────────────────────────────────────
    chunk_size: int = 800
    chunk_overlap: int = 200

    # ── Server ────────────────────────────────────────────────
    port: int = 8000

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — loaded once at startup."""
    return Settings()
