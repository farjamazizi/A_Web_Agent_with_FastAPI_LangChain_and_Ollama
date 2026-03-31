"""ASGI entrypoint for local development and deployment."""

from ask_web_agent.api import create_app

app = create_app()
