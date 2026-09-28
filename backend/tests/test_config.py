"""Unit tests for SearchMind configuration."""

import os
from unittest.mock import patch
from app.config import Settings


def test_default_config():
    """Verify default configuration values."""
    settings = Settings(
        HINDSIGHT_API_LLM_API_KEY="",
        _env_file=None,
    )
    assert settings.ENVIRONMENT == "development"
    assert settings.HOST == "127.0.0.1"
    assert settings.PORT == 8000
    assert settings.HINDSIGHT_API_DATABASE_URL == "pg0"
    assert settings.HINDSIGHT_PROFILE == "searchmind"
    assert settings.is_llm_configured is False


def test_llm_configured_detection():
    """Verify detection of placeholder vs real LLM API keys."""
    # Empty key
    s1 = Settings(HINDSIGHT_API_LLM_API_KEY="", _env_file=None)
    assert s1.is_llm_configured is False

    # Placeholder key from .env.example
    s2 = Settings(HINDSIGHT_API_LLM_API_KEY="your_llm_api_key_here", _env_file=None)
    assert s2.is_llm_configured is False

    s3 = Settings(HINDSIGHT_API_LLM_API_KEY="your_api_key", _env_file=None)
    assert s3.is_llm_configured is False

    # Valid key
    s4 = Settings(HINDSIGHT_API_LLM_API_KEY="sk-valid-api-key-12345", _env_file=None)
    assert s4.is_llm_configured is True


def test_custom_provider_settings():
    """Verify custom LLM provider configuration."""
    settings = Settings(
        HINDSIGHT_API_LLM_PROVIDER="gemini",
        HINDSIGHT_API_LLM_MODEL="gemini-1.5-flash",
        HINDSIGHT_API_LLM_API_KEY="test-gemini-key",
        _env_file=None,
    )
    assert settings.HINDSIGHT_API_LLM_PROVIDER == "gemini"
    assert settings.HINDSIGHT_API_LLM_MODEL == "gemini-1.5-flash"
    assert settings.is_llm_configured is True


def test_demo_mode_configuration():
    """Verify SEARCHMIND_DEMO_MODE setting defaults to False and can be toggled."""
    s_default = Settings(HINDSIGHT_API_LLM_API_KEY="", _env_file=None)
    assert s_default.SEARCHMIND_DEMO_MODE is False

    s_demo = Settings(SEARCHMIND_DEMO_MODE=True, _env_file=None)
    assert s_demo.SEARCHMIND_DEMO_MODE is True

