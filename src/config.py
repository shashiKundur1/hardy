from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Hardy"
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./hardy.db"
    session_secret: str = ""
    session_max_age: int = 60 * 60 * 24 * 14

    mesh_api_key: str = ""
    mesh_base_url: str = "https://api.meshapi.ai/v1"
    mesh_chat_model: str = "openai/gpt-4o"
    mesh_embed_model: str = "openai/text-embedding-3-small"
    mesh_timeout_seconds: int = 60

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "products"
    embedding_dim: int = 1536

    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "hardy"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    digest_hour: int = 8
    digest_timezone: str = "Asia/Kolkata"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
