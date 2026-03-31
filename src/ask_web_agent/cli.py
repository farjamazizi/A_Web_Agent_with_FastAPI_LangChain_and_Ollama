"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from typing import Any

import uvicorn

from .agent import ToolCallingAgent
from .api import create_app
from .config import get_settings
from .tools import compare_weather, get_current_weather, search_web


def _make_agent() -> ToolCallingAgent:
    settings = get_settings()
    return ToolCallingAgent(
        settings=settings,
        tools={
            "compare_weather": compare_weather,
            "get_current_weather": get_current_weather,
            "search_web": search_web,
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ask-web-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    weather_parser = subparsers.add_parser("weather", help="Run the weather demo tool.")
    weather_parser.add_argument("city")
    weather_parser.add_argument("--unit", default="celsius")

    search_parser = subparsers.add_parser("search", help="Run the web search tool.")
    search_parser.add_argument("query")
    search_parser.add_argument("--max-results", type=int, default=None)

    ask_parser = subparsers.add_parser("ask", help="Ask the model to decide on tool usage.")
    ask_parser.add_argument("question")

    serve_parser = subparsers.add_parser("serve", help="Run the FastAPI server.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "weather":
        print(get_current_weather(city=args.city, unit=args.unit))
        return 0

    if args.command == "search":
        settings = get_settings()
        max_results = args.max_results or settings.web_search_max_results
        print(json.dumps(search_web(args.query, max_results=max_results), indent=2))
        return 0

    if args.command == "ask":
        response: dict[str, Any] = _make_agent().answer(args.question)
        print(json.dumps(response, indent=2))
        return 0

    if args.command == "serve":
        uvicorn.run(create_app(), host=args.host, port=args.port)
        return 0

    parser.error("Unknown command")
    return 2
