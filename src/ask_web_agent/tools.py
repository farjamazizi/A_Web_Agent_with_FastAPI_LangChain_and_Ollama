"""Tool implementations for the web agent."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

import httpx
from ddgs import DDGS
from openai import OpenAI

from .config import get_settings

WeatherUnit = Literal["celsius", "fahrenheit"]

WEATHER_CODE_LABELS = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "slight snow",
    73: "moderate snow",
    75: "heavy snow",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
}


@lru_cache(maxsize=1)
def _http_client() -> httpx.Client:
    settings = get_settings()
    return httpx.Client(timeout=settings.request_timeout_seconds)


@lru_cache(maxsize=1)
def _model_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def list_available_tools() -> list[dict[str, str]]:
    """List the tools available in the project."""

    return [
        {
            "name": "get_current_weather",
            "description": "Get live current weather for a city using Open-Meteo.",
        },
        {
            "name": "compare_weather",
            "description": "Compare current weather between two cities.",
        },
        {
            "name": "search_web",
            "description": "Search the web with DuckDuckGo and normalize the results.",
        },
        {
            "name": "check_model_status",
            "description": "Check whether the configured OpenAI-compatible model backend is reachable.",
        },
        {
            "name": "list_available_tools",
            "description": "List the tools exposed by this project.",
        },
    ]


def _resolve_city(city: str) -> dict[str, Any]:
    response = _http_client().get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results") or []
    if not results:
        raise ValueError(f"Could not find weather coordinates for '{city}'.")
    return results[0]


def _fetch_weather_snapshot(city: str, unit: WeatherUnit = "celsius") -> dict[str, Any]:
    location = _resolve_city(city)
    response = _http_client().get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": [
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "weather_code",
                "wind_speed_10m",
            ],
            "temperature_unit": unit,
            "wind_speed_unit": "kmh",
            "timezone": "auto",
        },
    )
    response.raise_for_status()
    forecast = response.json()
    current = forecast.get("current") or {}
    if not current:
        raise ValueError(f"Weather service returned no current conditions for '{city}'.")

    return {
        "resolved_name": location.get("name", city),
        "country": location.get("country", ""),
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "temperature": current.get("temperature_2m"),
        "apparent_temperature": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "weather_code": current.get("weather_code"),
        "weather_description": WEATHER_CODE_LABELS.get(
            current.get("weather_code"),
            "unknown conditions",
        ),
        "unit": unit,
    }


def _format_weather(snapshot: dict[str, Any]) -> str:
    temperature_unit = "C" if snapshot["unit"] == "celsius" else "F"
    city_label = snapshot["resolved_name"]
    if snapshot["country"]:
        city_label = f"{city_label}, {snapshot['country']}"

    return (
        f"{city_label} is currently {snapshot['temperature']} {temperature_unit} "
        f"and feels like {snapshot['apparent_temperature']} {temperature_unit}. "
        f"Conditions are {snapshot['weather_description']} with humidity at "
        f"{snapshot['humidity']}% and wind around {snapshot['wind_speed']} km/h."
    )


def get_current_weather(city: str, unit: WeatherUnit = "celsius") -> str:
    """Get live current weather for a city."""

    return _format_weather(_fetch_weather_snapshot(city=city, unit=unit))


def compare_weather(
    city_a: str,
    city_b: str,
    unit: WeatherUnit = "celsius",
) -> str:
    """Compare current weather between two cities."""

    snapshot_a = _fetch_weather_snapshot(city_a, unit=unit)
    snapshot_b = _fetch_weather_snapshot(city_b, unit=unit)
    warmer_city = (
        snapshot_a["resolved_name"]
        if snapshot_a["temperature"] >= snapshot_b["temperature"]
        else snapshot_b["resolved_name"]
    )
    temperature_unit = "C" if unit == "celsius" else "F"

    return (
        f"{_format_weather(snapshot_a)} "
        f"{_format_weather(snapshot_b)} "
        f"{warmer_city} is warmer right now based on the live temperature reading "
        f"({snapshot_a['temperature']} {temperature_unit} vs {snapshot_b['temperature']} {temperature_unit})."
    )


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
                "Make sure your OpenAI-compatible server is running and the configured model is loaded."
            ),
            "error": str(exc),
        }
