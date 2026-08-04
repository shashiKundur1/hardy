from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mesh_api_key: str = ""
    mesh_base_url: str = "https://api.meshapi.ai/v1"
    mesh_chat_model: str = "openai/gpt-4o"
    mesh_embed_model: str = "openai/text-embedding-3-small"
    embedding_dim: int = 1536

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "products"

    database_url: str = "sqlite+aiosqlite:///./hardy.db"
    session_secret: str = ""

    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "hardy"

    smtp_host: str = ""
    smtp_user: str = ""
    smtp_pass: str = ""

    digest_hour: int = 8
    digest_timezone: str = "Asia/Kolkata"

    trigger_event_threshold: int = 12
    trigger_min_events: int = 5
    trigger_rate_floor_minutes: int = 10
    retrieval_k: int = 5
    max_refine_loops: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
