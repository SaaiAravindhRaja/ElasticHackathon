from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    es_url: str
    es_api_key: str
    openai_api_key: str
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"

    chunk_size: int = 800
    chunk_overlap: int = 100
    embedding_model: str = "text-embedding-3-small"
    bulk_batch_size: int = 50
    openai_model: str = "gpt-4o-mini"
    rag_top_k: int = 8
    api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
