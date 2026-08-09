import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "DataForge AI"
    VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite+aiosqlite:///./dataforge.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-4o"
    OPENROUTER_SITE_URL: str = "http://localhost:3000"
    OPENROUTER_SITE_NAME: str = "DataForge AI"
    STORAGE_DIR: str = "./data_scratch"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
