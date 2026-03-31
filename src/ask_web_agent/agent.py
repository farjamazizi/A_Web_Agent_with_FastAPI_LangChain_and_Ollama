"""LangChain agent workflow."""

from __future__ import annotations

import json
from typing import Any

from langchain.agents import AgentType, initialize_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

from .config import Settings
from .tools import (
    check_model_status,
    compare_weather,
    get_current_weather,
    list_available_tools,
    search_web,
)


class AgentExecutionError(RuntimeError):
    """Raised when the model or tool agent cannot complete a request."""


def _json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=True)


class LangChainWebAgent:
    """Minimal LangChain wrapper around an OpenAI-compatible chat model."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm = ChatOpenAI(
            model=settings.model_name,
            temperature=settings.temperature,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.executor = initialize_agent(
            tools=self._build_tools(),
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

    def _build_tools(self) -> list[Tool]:
        return [
            Tool(
                name="get_current_weather",
                func=get_current_weather,
                description=(
                    "Use this to get live current weather for one city. "
                    "Input should be the city name and optionally a unit."
                ),
            ),
            Tool(
                name="compare_weather",
                func=lambda input_text: self._compare_weather_from_text(input_text),
                description=(
                    "Use this to compare weather between two cities. "
                    "Input format: city_a | city_b | unit. "
                    "Example: San Diego | Boston | celsius"
                ),
            ),
            Tool(
                name="search_web",
                func=lambda query: _json_dump(search_web(query, self.settings.web_search_max_results)),
                description=(
                    "Use this to search the web when the question needs fresh information. "
                    "Input should be a search query string."
                ),
            ),
            Tool(
                name="check_model_status",
                func=lambda _: _json_dump(check_model_status()),
                description="Use this to inspect model backend availability.",
            ),
            Tool(
                name="list_available_tools",
                func=lambda _: _json_dump(list_available_tools()),
                description="Use this to see which tools the agent can call.",
            ),
        ]

    def _compare_weather_from_text(self, input_text: str) -> str:
        parts = [part.strip() for part in input_text.split("|")]
        if len(parts) < 2:
            raise ValueError("compare_weather expects 'city_a | city_b | unit'.")
        city_a, city_b = parts[0], parts[1]
        unit = parts[2] if len(parts) > 2 and parts[2] else "celsius"
        return compare_weather(city_a=city_a, city_b=city_b, unit=unit)

    def answer(self, question: str) -> dict[str, Any]:
        """Run the LangChain agent and normalize its response."""

        try:
            result = self.executor.invoke({"input": question})
        except Exception as exc:
            raise AgentExecutionError(str(exc)) from exc

        intermediate_steps = result.get("intermediate_steps", [])
        steps = []
        for action, observation in intermediate_steps:
            steps.append(
                {
                    "tool": getattr(action, "tool", "unknown"),
                    "tool_input": getattr(action, "tool_input", ""),
                    "log": getattr(action, "log", ""),
                    "observation": observation if isinstance(observation, str) else _json_dump(observation),
                }
            )

        return {
            "mode": "agent",
            "content": result.get("output", ""),
            "steps": steps,
        }
