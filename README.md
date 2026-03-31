# Ask Web Agent

Ask Web Agent is a small full-stack demo that turns the original `web_agent.ipynb` notebook into a reusable Python package with:

- a FastAPI backend
- a React frontend
- an Ollama-compatible LLM tool-calling flow
- direct tool endpoints for weather, comparison, search, tool discovery, and model status

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

## Features

- `POST /ask` lets the model choose a tool from a natural-language question
- `POST /weather` returns weather text for one city
- `POST /compare-weather` compares weather between two cities
- `POST /search` runs DuckDuckGo search through `ddgs`
- `GET /tools` lists the project tools
- `GET /model-status` checks whether the configured model backend is reachable
- React frontend for trying the backend from a browser

## Backend setup

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Run the API:

```bash
uvicorn app.backend.main:app --reload
```

Backend URLs:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## Frontend setup

From the frontend directory:

```bash
cd app/frontend
npm install
npm run dev
```

Frontend URL:

- `http://127.0.0.1:5173`

The frontend expects the API at `http://127.0.0.1:8000` by default.

If your backend runs elsewhere:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## Model configuration

The backend is configured through environment variables:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `MODEL_NAME`
- `MODEL_TEMPERATURE`
- `WEB_SEARCH_MAX_RESULTS`

Default values target an Ollama-compatible local server:

- `OPENAI_BASE_URL=http://localhost:11434/v1`
- `MODEL_NAME=llama3.2:3b`

Typical Ollama flow:

```bash
ollama serve
ollama list
ollama pull llama3.2:3b
```

## Available tools

Current tools live in [tools.py](/home/farjam/python_web_agent_llm_demo/src/ask_web_agent/tools.py):

- `get_current_weather`
- `compare_weather`
- `search_web`
- `check_model_status`
- `list_available_tools`

## API endpoints

- `GET /health`
- `GET /tools`
- `GET /model-status`
- `POST /weather`
- `POST /compare-weather`
- `POST /search`
- `POST /ask`

## Example requests

Weather:

```bash
curl -X POST http://127.0.0.1:8000/weather \
  -H "Content-Type: application/json" \
  -d '{"city":"San Diego","unit":"celsius"}'
```

Compare weather:

```bash
curl -X POST http://127.0.0.1:8000/compare-weather \
  -H "Content-Type: application/json" \
  -d '{"city_a":"San Diego","city_b":"Boston","unit":"celsius"}'
```

Ask the agent:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Can you compare the weather between San Diego and Boston?"}'
```

## CLI usage

After installing the Python package:

```bash
ask-web-agent weather "San Diego"
ask-web-agent search "Boston weather today"
ask-web-agent ask "Can you compare the weather between San Diego and Boston?"
```

## Tests

Run the tests from the project root:

```bash
pytest -q tests/test_api.py tests/test_schemas.py
```

## Notes

- The weather tool currently returns demo weather text rather than live weather data.
- The ask flow depends on an OpenAI-compatible model backend, such as Ollama.
- The frontend is a Vite + React app and the backend allows local CORS for port `5173`.
