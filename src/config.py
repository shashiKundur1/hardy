from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Hardy"
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = "sqlite+aiosqlite:///./hardy.db"
    session_secret: str = ""
    session_max_age: int = 60 * 60 * 24 * 14
    https_only: bool = False

    cors_origins: str = ""

    mesh_api_key: str = ""
    mesh_base_url: str = "https://api.meshapi.ai/v1"
    mesh_chat_model: str = "openai/gpt-4o"
    mesh_embed_model: str = "openai/text-embedding-3-small"
    mesh_timeout_seconds: int = 60

    qdrant_url: str = ""
    qdrant_path: str = "./qdrant_data"
    qdrant_collection: str = "products"
    embedding_dim: int = 1536

    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "hardy"

    public_base_url: str = "http://localhost:8000"
    scheduler_enabled: bool = True

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    digest_hour: int = 8
    digest_timezone: str = "Asia/Kolkata"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
