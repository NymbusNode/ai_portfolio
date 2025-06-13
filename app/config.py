from pydantic_settings import BaseSettings, SettingsConfigDict
from .utils import load_file_text

class Settings(BaseSettings):
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    default_model: str = "gpt-4o"
    embed_model: str = "text-embedding-3-small"
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/portfolio_ai"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()