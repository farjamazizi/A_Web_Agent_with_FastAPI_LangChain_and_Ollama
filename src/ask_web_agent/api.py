"""FastAPI application."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agent import ToolCallError, ToolCallingAgent
from .config import get_settings
from .tools import (
    check_model_status,
    compare_weather,
    get_current_weather,
    list_available_tools,
    search_web,
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


class WeatherRequest(BaseModel):
    city: str = Field(..., min_length=1)
    unit: str = Field(default="celsius")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    max_results: int | None = Field(default=None, ge=1, le=20)


class CompareWeatherRequest(BaseModel):
    city_a: str = Field(..., min_length=1)
    city_b: str = Field(..., min_length=1)
    unit: str = Field(default="celsius")


@lru_cache(maxsize=1)
def _build_agent() -> ToolCallingAgent:
    settings = get_settings()
    return ToolCallingAgent(
        settings=settings,
        tools={
            "check_model_status": check_model_status,
            "compare_weather": compare_weather,
            "get_current_weather": get_current_weather,
            "list_available_tools": list_available_tools,
            "search_web": search_web,
        },
    )


def create_app() -> FastAPI:
    app = FastAPI(title="Ask Web Agent", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/tools")
    def tools() -> dict[str, list[dict[str, str]]]:
        return {"tools": list_available_tools()}

    @app.get("/model-status")
    def model_status() -> dict[str, Any]:
        return check_model_status()

    @app.post("/weather")
    def weather(request: WeatherRequest) -> dict[str, str]:
        return {
            "result": get_current_weather(city=request.city, unit=request.unit),
        }

    @app.post("/compare-weather")
    def compare_weather_endpoint(request: CompareWeatherRequest) -> dict[str, str]:
        return {
            "result": compare_weather(
                city_a=request.city_a,
                city_b=request.city_b,
                unit=request.unit,
            ),
        }

    @app.post("/search")
    def search(request: SearchRequest) -> dict[str, Any]:
        settings = get_settings()
        max_results = request.max_results or settings.web_search_max_results
        return {"results": search_web(request.query, max_results=max_results)}

    @app.post("/ask")
    def ask(request: AskRequest) -> dict[str, Any]:
        try:
            return _build_agent().answer(request.question)
        except ToolCallError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "The model backend could not answer the request. "
                    "Make sure Ollama is running, the configured model is available, "
                    "and the OpenAI-compatible endpoint is reachable."
                ),
            ) from exc

    return app
