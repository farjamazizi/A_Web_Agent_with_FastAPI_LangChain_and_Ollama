from fastapi import HTTPException

import ask_web_agent.api as api_module
from ask_web_agent.api import AskRequest, CompareWeatherRequest, SearchRequest, WeatherRequest, create_app


def _get_endpoint(path: str):
    app = create_app()
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise AssertionError(f"Route {path} was not found")


def test_health_endpoint() -> None:
    endpoint = _get_endpoint("/health")

    assert endpoint() == {"status": "ok"}


def test_weather_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        api_module,
        "get_current_weather",
        lambda city, unit="celsius": f"Weather for {city} in {unit}",
    )
    endpoint = _get_endpoint("/weather")
    response = endpoint(WeatherRequest(city="San Diego", unit="celsius"))

    assert "San Diego" in response["result"]


def test_compare_weather_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        api_module,
        "compare_weather",
        lambda city_a, city_b, unit="celsius": f"{city_a} vs {city_b} in {unit}",
    )
    endpoint = _get_endpoint("/compare-weather")
    response = endpoint(
        CompareWeatherRequest(city_a="San Diego", city_b="Boston", unit="celsius")
    )

    assert "San Diego" in response["result"]
    assert "Boston" in response["result"]


def test_search_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        api_module,
        "search_web",
        lambda query, max_results=5: [{"title": query, "url": "https://example.com", "snippet": str(max_results)}],
    )
    endpoint = _get_endpoint("/search")
    response = endpoint(SearchRequest(query="weather", max_results=2))

    assert response["results"][0]["title"] == "weather"


def test_tools_endpoint() -> None:
    endpoint = _get_endpoint("/tools")
    response = endpoint()

    names = {tool["name"] for tool in response["tools"]}
    assert "compare_weather" in names
    assert "check_model_status" in names


def test_tool_schemas_endpoint() -> None:
    endpoint = _get_endpoint("/tool-schemas")
    response = endpoint()

    names = {tool["name"] for tool in response["tools"]}
    assert "get_current_weather" in names
    assert "search_web" in names


def test_model_status_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        api_module,
        "check_model_status",
        lambda: {
            "backend_reachable": True,
            "configured_model": "llama3.2:3b",
            "model_available": True,
            "base_url": "http://localhost:11434/v1",
            "message": "ok",
        },
    )

    endpoint = _get_endpoint("/model-status")
    response = endpoint()

    assert response["backend_reachable"] is True
    assert response["configured_model"] == "llama3.2:3b"


def test_ask_returns_agent_payload(monkeypatch) -> None:
    class StubAgent:
        def answer(self, question: str) -> dict[str, str]:
            return {"mode": "agent", "content": f"Answered: {question}", "steps": []}

    monkeypatch.setattr(api_module, "_build_agent", lambda: StubAgent())

    endpoint = _get_endpoint("/ask")
    response = endpoint(AskRequest(question="What is the weather in Boston?"))

    assert response["mode"] == "agent"
    assert "Boston" in response["content"]


def test_ask_returns_502_when_model_backend_fails(monkeypatch) -> None:
    class BrokenAgent:
        def answer(self, question: str) -> dict[str, str]:
            raise api_module.AgentExecutionError("backend unavailable")

    monkeypatch.setattr(api_module, "_build_agent", lambda: BrokenAgent())

    endpoint = _get_endpoint("/ask")

    try:
        endpoint(AskRequest(question="What is the weather in Boston?"))
    except HTTPException as exc:
        assert exc.status_code == 502
        assert "OpenAI-compatible endpoint" in exc.detail
        assert "backend unavailable" in exc.detail
    else:
        raise AssertionError("Expected HTTPException for backend failure")
