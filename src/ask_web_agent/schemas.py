"""Schema helpers for tool calling."""

from __future__ import annotations

import inspect
from typing import Any, get_args, get_origin


def _annotation_to_json_type(annotation: Any) -> str:
    if annotation in (str, inspect._empty):
        return "string"
    if annotation in (int, float):
        return "number"
    if annotation is bool:
        return "boolean"
    if get_origin(annotation) is list:
        return "array"
    return "string"


def _enum_values(annotation: Any) -> list[str] | None:
    if get_origin(annotation) is None:
        return None
    values = get_args(annotation)
    if values and all(isinstance(value, str) for value in values):
        return list(values)
    return None


def to_schema(fn: Any) -> dict[str, Any]:
    """Build a simple JSON schema for a Python callable."""

    sig = inspect.signature(fn)
    properties: dict[str, Any] = {}

    for name, param in sig.parameters.items():
        annotation = param.annotation
        prop: dict[str, Any] = {
            "type": _annotation_to_json_type(annotation),
            "description": f"Argument {name}",
        }
        enum_values = _enum_values(annotation)
        if enum_values:
            prop["enum"] = enum_values
        properties[name] = prop

    return {
        "name": fn.__name__,
        "description": (fn.__doc__ or "").strip().splitlines()[0],
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": [
                name
                for name, param in sig.parameters.items()
                if param.default is inspect._empty
            ],
        },
    }
