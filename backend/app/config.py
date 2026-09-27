"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


# Look for .env in the backend folder or workspace root
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """SearchMind application and Hindsight runtime settings."""

    # Server Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Hindsight Core Configuration
    HINDSIGHT_API_LLM_PROVIDER: str = "openai"
    HINDSIGHT_API_LLM_API_KEY: str = ""
    HINDSIGHT_API_LLM_MODEL: str = "gpt-4o-mini"
    HINDSIGHT_API_LLM_BASE_URL: Optional[str] = None
    HINDSIGHT_API_DATABASE_URL: str = "pg0"
    HINDSIGHT_PROFILE: str = "searchmind"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH if ENV_FILE_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_llm_configured(self) -> bool:
        """Return True if an actual LLM API key has been provided."""
        key = self.HINDSIGHT_API_LLM_API_KEY.strip()
        if not key:
            return False
        # Guard against placeholder values from .env.example
        placeholder_indicators = [
            "your_llm_api_key_here",
            "your_api_key",
            "placeholder",
            "changeme",
        ]
        return not any(indicator in key.lower() for indicator in placeholder_indicators)


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings."""
    return Settings()
