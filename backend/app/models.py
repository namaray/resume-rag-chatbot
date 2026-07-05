"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat question from the frontend."""
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The question to ask about the resume/projects.",
        examples=["What is Pangochain?", "What are his main skills?"],
    )


class SourceReference(BaseModel):
    """A source chunk that was used to generate the answer."""
    text: str = Field(description="The relevant text excerpt.")
    source_file: str = Field(description="The source document filename.")
    heading: str = Field(default="", description="Section heading, if available.")
    score: float = Field(description="Similarity score (0-1).")


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""
    answer: str = Field(description="The generated answer.")
    sources: list[SourceReference] = Field(
        default_factory=list,
        description="Source chunks used to generate the answer.",
    )
    model_used: str = Field(default="", description="Which LLM model was used.")
    response_time_ms: int = Field(
        default=0, description="Total response time in milliseconds."
    )


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="ok")
    index_loaded: bool = Field(default=False)
    chunk_count: int = Field(default=0)
    model: str = Field(default="")
