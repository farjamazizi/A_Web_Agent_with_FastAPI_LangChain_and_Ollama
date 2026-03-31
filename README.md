# Ask Web Agent

Ask Web Agent turns the original [`web_agent.ipynb`](/home/farjam/python_web_agent_llm_demo/web_agent.ipynb) notebook into a reusable full-stack project with:

- a Python package under [`src/ask_web_agent`](/home/farjam/python_web_agent_llm_demo/src/ask_web_agent)
- a FastAPI backend under [`app/backend`](/home/farjam/python_web_agent_llm_demo/app/backend)
- a React + Vite frontend under [`app/frontend`](/home/farjam/python_web_agent_llm_demo/app/frontend)
- a LangChain-powered agent that can decide when to use tools
- real API integrations for live weather and web search

## What changed from the notebook

The notebook demonstrates:

- simple Python tools
- manual tool-call parsing
- schema generation
- LangChain agent setup
- a web-search agent

This project packages those ideas into a proper app:

- installable module
- configurable runtime settings
- backend API endpoints
- browser UI
- CLI
- tests

## Project layout

```text
.
├── app/
│   ├── backend/
│   │   └── main.py
│   └── frontend/
│       ├── package.json
│       └── src/
├── src/
│   └── ask_web_agent/
├── tests/
├── pyproject.toml
└── web_agent.ipynb
```

## Backend features

- `POST /ask` runs a LangChain agent against your configured model
- `POST /weather` returns live weather from Open-Meteo
- `POST /compare-weather` compares live weather between two cities
- `POST /search` runs DuckDuckGo search through `ddgs`
- `GET /tools` lists project tools
- `GET /tool-schemas` exposes simple JSON schemas for those tools
- `GET /model-status` checks whether your model backend is reachable

## Model support

The backend uses `langchain-openai` with an OpenAI-compatible chat endpoint, so you can point it at:

- Ollama's OpenAI-compatible API
- OpenAI
- another compatible local or hosted model gateway

Environment variables:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `MODEL_NAME`
- `MODEL_TEMPERATURE`
- `WEB_SEARCH_MAX_RESULTS`
- `REQUEST_TIMEOUT_SECONDS`
- `ALLOWED_ORIGINS`

Example local defaults:

```bash
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
export MODEL_NAME=llama3.2:3b
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Run the backend

```bash
uvicorn app.backend.main:app --reload
```

or

```bash
python -m ask_web_agent.cli serve
```

Backend URLs:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## Run the frontend

```bash
cd app/frontend
npm install
npm run dev
```

Frontend URL:

- `http://127.0.0.1:5173`

If your API runs elsewhere:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## CLI examples

```bash
ask-web-agent weather "Stockholm"
ask-web-agent compare-weather "San Diego" "Boston"
ask-web-agent search "latest weather in Boston"
ask-web-agent ask "Compare the weather in Stockholm and Berlin and summarize it."
```

## Testing

```bash
pytest -q
```

## Notes

- Weather data comes from Open-Meteo.
- Web search uses DuckDuckGo through `ddgs`.
- The LangChain agent uses a ReAct-style flow, which is usually more portable across local OpenAI-compatible backends than native tool-calling support.
