"""FastAPI application."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agent import AgentExecutionError, LangChainWebAgent
from .config import get_settings
from .schemas import to_schema
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
def _build_agent() -> LangChainWebAgent:
    return LangChainWebAgent(settings=get_settings())


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Ask Web Agent", version="0.2.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
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

    @app.get("/tool-schemas")
    def tool_schemas() -> dict[str, list[dict[str, Any]]]:
        return {
            "tools": [
                to_schema(get_current_weather),
                to_schema(compare_weather),
                to_schema(search_web),
                to_schema(check_model_status),
                to_schema(list_available_tools),
            ]
        }

    @app.get("/model-status")
    def model_status() -> dict[str, Any]:
        return check_model_status()

    @app.post("/weather")
    def weather(request: WeatherRequest) -> dict[str, str]:
        return {"result": get_current_weather(city=request.city, unit=request.unit)}

    @app.post("/compare-weather")
    def compare_weather_endpoint(request: CompareWeatherRequest) -> dict[str, str]:
        return {
            "result": compare_weather(
                city_a=request.city_a,
                city_b=request.city_b,
                unit=request.unit,
            )
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
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except AgentExecutionError as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "The model backend could not complete the request. "
                    "Make sure your OpenAI-compatible endpoint is reachable and the model is available. "
                    f"Backend error: {exc}"
                ),
            ) from exc

    return app
