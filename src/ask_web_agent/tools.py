"""Tool implementations."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from ddgs import DDGS
from openai import OpenAI

from .config import get_settings


def list_available_tools() -> list[dict[str, str]]:
    """List the tools available in the project."""

    return [
        {
            "name": "get_current_weather",
            "description": "Return a simple weather summary for one city.",
        },
        {
            "name": "compare_weather",
            "description": "Compare the weather between two cities.",
        },
        {
            "name": "search_web",
            "description": "Search the web and return normalized search results.",
        },
        {
            "name": "check_model_status",
            "description": "Check whether the configured model backend is reachable.",
        },
        {
            "name": "list_available_tools",
            "description": "List the tools exposed by this project.",
        },
    ]


def get_current_weather(
    city: str,
    unit: Literal["celsius", "fahrenheit"] = "celsius",
) -> str:
    """Return the current weather as a human-readable sentence."""

    unit_symbol = "C" if unit == "celsius" else "F"
    return f"It is 23 {unit_symbol} and sunny in {city}."


def compare_weather(
    city_a: str,
    city_b: str,
    unit: Literal["celsius", "fahrenheit"] = "celsius",
) -> str:
    """Compare the weather between two cities."""

    weather_a = get_current_weather(city_a, unit=unit)
    weather_b = get_current_weather(city_b, unit=unit)
    return f"{city_a}: {weather_a} {city_b}: {weather_b}"


def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search the web and return normalized search results."""

    results: list[dict[str, str]] = []
    with DDGS() as ddgs:
        for result in ddgs.text(query, max_results=max_results):
            results.append(
                {
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                }
            )
    return results


@lru_cache(maxsize=1)
def _model_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def check_model_status() -> dict[str, str | bool]:
    """Check whether the configured model backend is reachable."""

    settings = get_settings()
    try:
        models = _model_client().models.list()
        model_ids = {model.id for model in models.data}
        model_available = settings.model_name in model_ids
        return {
            "backend_reachable": True,
            "configured_model": settings.model_name,
            "model_available": model_available,
            "base_url": settings.openai_base_url,
            "message": (
                f"Model '{settings.model_name}' is available."
                if model_available
                else f"Backend is reachable, but model '{settings.model_name}' was not found."
            ),
        }
    except Exception as exc:
        return {
            "backend_reachable": False,
            "configured_model": settings.model_name,
            "model_available": False,
            "base_url": settings.openai_base_url,
            "message": (
                "Could not reach the configured model backend. "
                "Make sure Ollama is running and the OpenAI-compatible endpoint is available."
            ),
            "error": str(exc),
        }
