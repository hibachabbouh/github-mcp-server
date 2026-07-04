from groq import AsyncGroq
from src.config import settings
from src.utils.exceptions import LLMError
from src.utils.logger import get_logger

logger = get_logger(__name__)

_groq: AsyncGroq | None = None


def get_groq_client() -> AsyncGroq:
    global _groq
    if _groq is None:
        _groq = AsyncGroq(api_key=settings.groq_api_key, max_retries=0)
        logger.info("Groq client initialized", model=settings.llm_model)
    return _groq


async def complete(system: str, user: str) -> str:
    """Single-turn completion. Returns the assistant message text."""
    client = get_groq_client()
    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        raise LLMError(f"Groq API call failed: {e}") from e
