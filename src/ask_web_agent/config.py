"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "ollama")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    model_name: str = os.getenv("MODEL_NAME", "llama3.2:3b")
    temperature: float = float(os.getenv("MODEL_TEMPERATURE", "0.1"))
    web_search_max_results: int = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))


def get_settings() -> Settings:
    """Return application settings."""

    return Settings()
