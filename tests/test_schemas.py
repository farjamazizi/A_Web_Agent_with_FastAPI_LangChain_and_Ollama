from typing import Literal

from ask_web_agent.agent import ToolCallError, parse_tool_call
from ask_web_agent.schemas import to_schema
import ask_web_agent.tools as tools_module
from ask_web_agent.tools import (
    check_model_status,
    compare_weather,
    get_current_weather,
    list_available_tools,
    search_web,
)


def demo_tool(city: str, unit: Literal["celsius", "fahrenheit"] = "celsius") -> str:
    """Return a demo result."""

    return f"{city} ({unit})"


def test_to_schema_builds_required_and_enum_fields() -> None:
    schema = to_schema(demo_tool)

    assert schema["name"] == "demo_tool"
    assert schema["parameters"]["required"] == ["city"]
    assert schema["parameters"]["properties"]["unit"]["enum"] == [
        "celsius",
        "fahrenheit",
    ]


def test_parse_tool_call_extracts_payload() -> None:
    payload = parse_tool_call('TOOL_CALL:{"name":"demo_tool","args":{"city":"Boston"}}')

    assert payload == {"name": "demo_tool", "args": {"city": "Boston"}}


def test_parse_tool_call_accepts_code_fenced_json() -> None:
    payload = parse_tool_call(
        'TOOL_CALL:\n```json\n{"name":"compare_weather","args":{"city_a":"San Diego","city_b":"Boston"}}\n```'
    )

    assert payload == {
        "name": "compare_weather",
        "args": {"city_a": "San Diego", "city_b": "Boston"},
    }


def test_parse_tool_call_rejects_invalid_json() -> None:
    try:
        parse_tool_call('TOOL_CALL:{"name":}')
    except ToolCallError:
        pass
    else:
        raise AssertionError("Expected ToolCallError for invalid JSON")


def test_compare_weather_mentions_both_cities() -> None:
    result = compare_weather("San Diego", "Boston")

    assert "San Diego" in result
    assert "Boston" in result


def test_get_current_weather_supports_fahrenheit() -> None:
    result = get_current_weather("Boston", unit="fahrenheit")

    assert "Boston" in result
    assert "23 F" in result


def test_list_available_tools_contains_expected_tools() -> None:
    tools = {tool["name"] for tool in list_available_tools()}

    assert "compare_weather" in tools
    assert "check_model_status" in tools


def test_search_web_normalizes_results(monkeypatch) -> None:
    class FakeDDGS:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def text(self, query: str, max_results: int = 5):
            assert query == "weather in boston"
            assert max_results == 2
            return [
                {
                    "title": "Boston Weather",
                    "href": "https://example.com/boston",
                    "body": "Forecast for Boston",
                },
                {
                    "title": "More Boston Weather",
                    "href": "https://example.com/boston-2",
                    "body": "Another forecast",
                },
            ]

    monkeypatch.setattr(tools_module, "DDGS", FakeDDGS)

    results = search_web("weather in boston", max_results=2)

    assert results == [
        {
            "title": "Boston Weather",
            "url": "https://example.com/boston",
            "snippet": "Forecast for Boston",
        },
        {
            "title": "More Boston Weather",
            "url": "https://example.com/boston-2",
            "snippet": "Another forecast",
        },
    ]


def test_check_model_status_reports_available_model(monkeypatch) -> None:
    class FakeModels:
        data = [type("Model", (), {"id": "llama3.2:3b"})()]

    class FakeClient:
        class models:
            @staticmethod
            def list():
                return FakeModels()

    monkeypatch.setattr(
        tools_module,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "model_name": "llama3.2:3b",
                "openai_base_url": "http://localhost:11434/v1",
                "openai_api_key": "ollama",
            },
        )(),
    )
    tools_module._model_client.cache_clear()
    monkeypatch.setattr(tools_module, "_model_client", lambda: FakeClient())

    result = check_model_status()

    assert result["backend_reachable"] is True
    assert result["model_available"] is True
    assert result["configured_model"] == "llama3.2:3b"


def test_check_model_status_reports_backend_error(monkeypatch) -> None:
    monkeypatch.setattr(
        tools_module,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "model_name": "llama3.2:3b",
                "openai_base_url": "http://localhost:11434/v1",
                "openai_api_key": "ollama",
            },
        )(),
    )
    tools_module._model_client.cache_clear()
    monkeypatch.setattr(
        tools_module,
        "_model_client",
        lambda: (_ for _ in ()).throw(RuntimeError("connection refused")),
    )

    result = check_model_status()

    assert result["backend_reachable"] is False
    assert result["model_available"] is False
    assert "Could not reach" in result["message"]
    assert "connection refused" in result["error"]
