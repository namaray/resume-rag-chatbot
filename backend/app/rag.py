"""
RAG pipeline — the core logic that retrieves relevant chunks
and generates grounded answers using Gemini.
"""

import time
import logging
from google import genai
from groq import Groq

from app.config import get_settings
from app.embeddings import embed_query
from app.vector_store import VectorStore
from app.models import ChatResponse, SourceReference

logger = logging.getLogger(__name__)

# ── System prompt that prevents hallucination ─────────────────

SYSTEM_PROMPT = """You are an AI assistant that answers questions about a person's resume, projects, and professional background. You are embedded in their portfolio website to help recruiters and interviewers learn about them.

STRICT RULES:
1. Answer ONLY using the provided context below. Do not use any external knowledge.
2. If the answer is not found in the context, say: "I don't have that information in my documents. You might want to ask about my projects, skills, or experience instead."
3. NEVER fabricate or invent skills, experiences, projects, certifications, or any claims about the person.
4. Be concise, professional, and helpful. Use a friendly but informative tone.
5. When relevant, mention which project or section the information comes from.
6. Format your responses using markdown for readability (bullet points, bold for emphasis).
7. Refer to the person in third person (e.g., "He has experience in..." or "His project Pangochain...") unless the context suggests otherwise.
"""

CONTEXT_TEMPLATE = """
--- RETRIEVED CONTEXT ---
{context}
--- END CONTEXT ---

Question: {question}
"""

# ── Blocked patterns for basic injection filtering ────────────

BLOCKED_PATTERNS = [
    "ignore previous",
    "ignore above",
    "disregard",
    "forget your instructions",
    "you are now",
    "pretend to be",
    "act as",
    "system prompt",
    "reveal your prompt",
]


def _check_input(question: str) -> str | None:
    """
    Basic input validation. Returns an error message if the input
    is problematic, or None if it's okay.
    """
    lower = question.lower().strip()

    # Check for prompt injection attempts
    for pattern in BLOCKED_PATTERNS:
        if pattern in lower:
            return (
                "I can only answer questions about the resume and projects. "
                "Please ask something like 'What is Pangochain?' or "
                "'What are his main skills?'"
            )

    return None


# Module-level Gemini client (initialized lazily)
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Get or create the Gemini client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def generate_answer(
    question: str,
    vector_store: VectorStore,
) -> ChatResponse:
    """
    Full RAG pipeline:
    1. Validate input
    2. Embed the question
    3. Retrieve relevant chunks
    4. Generate a grounded answer using Gemini

    Args:
        question: The user's question.
        vector_store: The loaded VectorStore instance.

    Returns:
        ChatResponse with the answer, sources, and metadata.
    """
    start_time = time.time()
    settings = get_settings()

    # ── Step 1: Input validation ──────────────────────────────
    error = _check_input(question)
    if error:
        return ChatResponse(
            answer=error,
            sources=[],
            model_used=settings.gemini_chat_model,
            response_time_ms=int((time.time() - start_time) * 1000),
        )

    # ── Step 2: Embed the question ────────────────────────────
    try:
        query_embedding = embed_query(question)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return ChatResponse(
            answer="Sorry, I'm having trouble processing your question right now. Please try again in a moment.",
            sources=[],
            model_used=settings.gemini_chat_model,
            response_time_ms=int((time.time() - start_time) * 1000),
        )

    # ── Step 3: Retrieve relevant chunks ──────────────────────
    try:
        results = vector_store.search(
            query_embedding,
            top_k=settings.top_k,
            threshold=settings.similarity_threshold,
        )
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        return ChatResponse(
            answer="Sorry, I couldn't search my documents right now. Please try again.",
            sources=[],
            model_used=settings.gemini_chat_model,
            response_time_ms=int((time.time() - start_time) * 1000),
        )

    # If no relevant chunks found, say so explicitly
    if not results:
        return ChatResponse(
            answer=(
                "I don't have specific information about that in my documents. "
                "Try asking about:\n"
                "- **Projects** like Pangochain or ML research\n"
                "- **Skills** and technical expertise\n"
                "- **Experience** and work history\n"
                "- **Education** and certifications"
            ),
            sources=[],
            model_used=settings.gemini_chat_model,
            response_time_ms=int((time.time() - start_time) * 1000),
        )

    # Build context from retrieved chunks
    context_parts = []
    sources = []
    for r in results:
        chunk = r["chunk"]
        score = r["score"]
        context_parts.append(
            f"[Source: {chunk.source_file}"
            f"{' — ' + chunk.heading if chunk.heading else ''}]\n"
            f"{chunk.text}"
        )
        sources.append(SourceReference(
            text=chunk.text[:200] + ("..." if len(chunk.text) > 200 else ""),
            source_file=chunk.source_file,
            heading=chunk.heading,
            score=score,
        ))

    context = "\n\n---\n\n".join(context_parts)

    # Log retrieved chunks for debugging
    logger.info(
        f"Query: '{question}' → {len(results)} chunks retrieved "
        f"(scores: {[f'{r['score']:.3f}' for r in results]})"
    )

    # ── Step 4: Generate answer with Gemini (or Fallback) ───────
    user_message = CONTEXT_TEMPLATE.format(context=context, question=question)
    model_used = settings.gemini_chat_model

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=settings.gemini_chat_model,
            contents=user_message,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )
        answer = response.text or "I wasn't able to generate a response. Please try again."
    except Exception as e:
        logger.error(f"Gemini generation failed: {e}. Attempting Groq fallback...")
        if settings.groq_api_key and settings.groq_api_key != "your_groq_api_key_here":
            try:
                groq_client = Groq(api_key=settings.groq_api_key)
                completion = groq_client.chat.completions.create(
                    model=settings.groq_chat_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.3,
                    max_tokens=1024,
                )
                answer = completion.choices[0].message.content or "I wasn't able to generate a response."
                model_used = settings.groq_chat_model
            except Exception as groq_e:
                logger.error(f"Groq generation failed: {groq_e}")
                answer = "I'm having trouble generating a response right now. Please try again in a moment."
        else:
            answer = (
                "I'm having trouble generating a response right now. "
                "This might be due to API rate limits. Please try again in a moment."
            )

    elapsed_ms = int((time.time() - start_time) * 1000)

    return ChatResponse(
        answer=answer,
        sources=sources,
        model_used=model_used,
        response_time_ms=elapsed_ms,
    )
