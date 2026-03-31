"""LLM tool-calling workflow."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from openai import OpenAI

from .config import Settings
from .schemas import to_schema

SYSTEM_PROMPT = (
    "You are an assistant that can call tools. "
    "When the user's request needs a tool, respond only with "
    'TOOL_CALL:{"name": <tool_name>, "args": { ... }} '
    "with valid JSON and no markdown fences. "
    "If no tool is needed, answer plainly."
)


class ToolCallError(ValueError):
    """Raised when a tool call cannot be parsed or executed."""


def parse_tool_call(raw_response: str) -> dict[str, Any] | None:
    """Extract a tool call payload from model output."""

    marker = "TOOL_CALL:"
    if marker not in raw_response:
        return None

    payload_text = raw_response.split(marker, maxsplit=1)[1].strip()
    payload_text = payload_text.removeprefix("```json").removeprefix("```").strip()
    payload_text = payload_text.removesuffix("```").strip()

    json_text = _extract_first_json_object(payload_text)
    if json_text is None:
        raise ToolCallError("Model returned invalid tool JSON.")

    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ToolCallError("Model returned invalid tool JSON.") from exc

    if "name" not in payload:
        raise ToolCallError("Tool call payload is missing 'name'.")

    payload.setdefault("args", {})
    return payload


def _extract_first_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(text)):
        char = text[index]

        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return None


class ToolCallingAgent:
    """Minimal OpenAI-compatible tool-calling wrapper."""

    def __init__(self, settings: Settings, tools: dict[str, Callable[..., Any]]) -> None:
        self.settings = settings
        self.tools = tools
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return [to_schema(tool) for tool in self.tools.values()]

    def decide(self, question: str) -> str:
        """Ask the model whether it wants to call a tool."""

        response = self.client.chat.completions.create(
            model=self.settings.model_name,
            temperature=self.settings.temperature,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "system",
                    "name": "tool_spec",
                    "content": json.dumps(self.get_tool_schemas()),
                },
                {"role": "user", "content": question},
            ],
        )
        return response.choices[0].message.content or ""

    def answer(self, question: str) -> dict[str, Any]:
        """Return either a direct answer or the result of one tool call."""

        raw_response = self.decide(question)
        payload = parse_tool_call(raw_response)
        if payload is None:
            return {"mode": "answer", "content": raw_response}

        tool_name = payload["name"]
        tool_args = payload.get("args", {})

        if tool_name not in self.tools:
            raise ToolCallError(f"Unknown tool '{tool_name}'.")

        result = self.tools[tool_name](**tool_args)
        return {
            "mode": "tool_call",
            "tool_name": tool_name,
            "tool_args": tool_args,
            "raw_response": raw_response,
            "result": result,
        }
