from openai import AsyncOpenAI
from app.config import get_settings

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=get_settings().openai_api_key)
    return _client


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts using text-embedding-3-small (1536 dims).
    Processes in batches of 100 to stay within OpenAI token limits.
    Returns vectors in the same order as input.
    """
    if not texts:
        return []

    settings = get_settings()
    client = get_openai_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), 100):
        batch = texts[i : i + 100]
        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=batch,
            encoding_format="float",
        )
        all_embeddings.extend(item.embedding for item in response.data)

    return all_embeddings


async def embed_single(text: str) -> list[float]:
    results = await embed_texts([text])
    return results[0]
