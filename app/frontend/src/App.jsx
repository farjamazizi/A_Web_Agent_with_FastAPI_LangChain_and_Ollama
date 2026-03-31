import { useEffect, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const defaultWeatherForm = {
  city: "San Diego",
  unit: "celsius"
};

const defaultCompareForm = {
  cityA: "San Diego",
  cityB: "Boston",
  unit: "celsius"
};

const defaultSearchForm = {
  query: "Boston weather today",
  maxResults: 5
};

const defaultAskQuestion = "Can you compare the weather between San Diego and Boston?";

function App() {
  const [health, setHealth] = useState({ status: "checking", detail: "Connecting to backend..." });
  const [toolCatalog, setToolCatalog] = useState([]);
  const [modelStatus, setModelStatus] = useState(null);
  const [weatherForm, setWeatherForm] = useState(defaultWeatherForm);
  const [weatherResult, setWeatherResult] = useState(null);
  const [compareForm, setCompareForm] = useState(defaultCompareForm);
  const [compareResult, setCompareResult] = useState(null);
  const [searchForm, setSearchForm] = useState(defaultSearchForm);
  const [searchResult, setSearchResult] = useState([]);
  const [askQuestion, setAskQuestion] = useState(defaultAskQuestion);
  const [askResult, setAskResult] = useState(null);
  const [activePanel, setActivePanel] = useState("ask");
  const [loading, setLoading] = useState({
    weather: false,
    compare: false,
    search: false,
    ask: false,
    tools: false,
    modelStatus: false
  });

  useEffect(() => {
    let cancelled = false;

    async function loadInitialData() {
      setLoading((current) => ({ ...current, tools: true, modelStatus: true }));

      try {
        const healthResponse = await fetch(`${API_BASE_URL}/health`);
        const healthData = await healthResponse.json();
        if (!cancelled) {
          setHealth({ status: healthData.status, detail: "Backend is ready." });
        }
      } catch (error) {
        if (!cancelled) {
          setHealth({
            status: "offline",
            detail: "Backend is unreachable. Start FastAPI on port 8000."
          });
        }
      }

      try {
        const toolsResponse = await fetch(`${API_BASE_URL}/tools`);
        const toolsData = await toolsResponse.json();
        if (!cancelled) {
          setToolCatalog(toolsData.tools || []);
        }
      } catch (error) {
        if (!cancelled) {
          setToolCatalog([]);
        }
      } finally {
        if (!cancelled) {
          setLoading((current) => ({ ...current, tools: false }));
        }
      }

      try {
        const statusResponse = await fetch(`${API_BASE_URL}/model-status`);
        const statusData = await statusResponse.json();
        if (!cancelled) {
          setModelStatus(statusData);
        }
      } catch (error) {
        if (!cancelled) {
          setModelStatus({
            backend_reachable: false,
            model_available: false,
            configured_model: "unknown",
            message: "Could not check model status."
          });
        }
      } finally {
        if (!cancelled) {
          setLoading((current) => ({ ...current, modelStatus: false }));
        }
      }
    }

    loadInitialData();
    return () => {
      cancelled = true;
    };
  }, []);

  async function request(path, payload) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok) {
      const detail = typeof data?.detail === "string" ? data.detail : "Request failed.";
      throw new Error(detail);
    }
    return data;
  }

  async function handleWeatherSubmit(event) {
    event.preventDefault();
    setLoading((current) => ({ ...current, weather: true }));
    try {
      const data = await request("/weather", weatherForm);
      setWeatherResult({ type: "success", content: data.result });
    } catch (error) {
      setWeatherResult({ type: "error", content: error.message });
    } finally {
      setLoading((current) => ({ ...current, weather: false }));
    }
  }

  async function handleCompareSubmit(event) {
    event.preventDefault();
    setLoading((current) => ({ ...current, compare: true }));
    try {
      const data = await request("/compare-weather", {
        city_a: compareForm.cityA,
        city_b: compareForm.cityB,
        unit: compareForm.unit
      });
      setCompareResult({ type: "success", content: data.result });
    } catch (error) {
      setCompareResult({ type: "error", content: error.message });
    } finally {
      setLoading((current) => ({ ...current, compare: false }));
    }
  }

  async function handleSearchSubmit(event) {
    event.preventDefault();
    setLoading((current) => ({ ...current, search: true }));
    try {
      const data = await request("/search", {
        query: searchForm.query,
        max_results: Number(searchForm.maxResults)
      });
      setSearchResult(data.results);
    } catch (error) {
      setSearchResult([{ title: "Search failed", url: "", snippet: error.message }]);
    } finally {
      setLoading((current) => ({ ...current, search: false }));
    }
  }

  async function handleAskSubmit(event) {
    event.preventDefault();
    setLoading((current) => ({ ...current, ask: true }));
    try {
      const data = await request("/ask", { question: askQuestion });
      setAskResult({ type: "success", content: data });
    } catch (error) {
      setAskResult({ type: "error", content: error.message });
    } finally {
      setLoading((current) => ({ ...current, ask: false }));
    }
  }

  async function refreshModelStatus() {
    setLoading((current) => ({ ...current, modelStatus: true }));
    try {
      const response = await fetch(`${API_BASE_URL}/model-status`);
      const data = await response.json();
      setModelStatus(data);
    } catch (error) {
      setModelStatus({
        backend_reachable: false,
        model_available: false,
        configured_model: "unknown",
        message: "Could not check model status."
      });
    } finally {
      setLoading((current) => ({ ...current, modelStatus: false }));
    }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">React Frontend</p>
          <h1>Explore your agent, tools, and model from one screen.</h1>
          <p className="hero-text">
            The UI now exposes direct tools, an agent question flow, live backend status, and a
            tool catalog pulled from your FastAPI project.
          </p>
          <div className="status-row">
            <span className={`status-pill status-${health.status}`}>{health.status}</span>
            <span className="status-text">{health.detail}</span>
          </div>
        </div>
        <div className="hero-card">
          <p className="card-label">Backend target</p>
          <p className="card-value">{API_BASE_URL}</p>
          <p className="card-note">
            If your API runs elsewhere, set <code>VITE_API_BASE_URL</code>.
          </p>
        </div>
      </section>

      <section className="dashboard-grid">
        <aside className="sidebar-stack">
          <section className="panel info-panel">
            <div className="info-panel-header">
              <div>
                <h2>Model status</h2>
                <p className="panel-copy">Checks whether Ollama and the configured model are reachable.</p>
              </div>
              <button className="ghost-button" onClick={refreshModelStatus} disabled={loading.modelStatus}>
                {loading.modelStatus ? "Refreshing..." : "Refresh"}
              </button>
            </div>
            <ModelStatusCard modelStatus={modelStatus} />
          </section>

          <section className="panel info-panel">
            <h2>Available tools</h2>
            <p className="panel-copy">Pulled from the backend so the frontend stays in sync.</p>
            <ToolCatalog tools={toolCatalog} loading={loading.tools} />
          </section>
        </aside>

        <section className="workspace">
          <div className="panel-tabs">
            <button className={tabClass(activePanel, "ask")} onClick={() => setActivePanel("ask")}>
              Ask Agent
            </button>
            <button
              className={tabClass(activePanel, "weather")}
              onClick={() => setActivePanel("weather")}
            >
              Weather
            </button>
            <button
              className={tabClass(activePanel, "compare")}
              onClick={() => setActivePanel("compare")}
            >
              Compare
            </button>
            <button className={tabClass(activePanel, "search")} onClick={() => setActivePanel("search")}>
              Search
            </button>
          </div>

          <div className="panel-grid">
            <section className={panelClass(activePanel, "ask")}>
              <h2>Ask the agent</h2>
              <p className="panel-copy">
                Send a natural-language request and let the model choose the right tool.
              </p>
              <form onSubmit={handleAskSubmit} className="stack">
                <label className="field">
                  <span>Question</span>
                  <textarea
                    rows="5"
                    value={askQuestion}
                    onChange={(event) => setAskQuestion(event.target.value)}
                  />
                </label>
                <button className="action-button" disabled={loading.ask}>
                  {loading.ask ? "Thinking..." : "Run /ask"}
                </button>
              </form>
              <ResultCard
                title="Agent response"
                result={askResult}
                renderSuccess={(data) => <AskResultView data={data} />}
              />
            </section>

            <section className={panelClass(activePanel, "weather")}>
              <h2>Weather tool</h2>
              <p className="panel-copy">Direct access to the single-city weather endpoint.</p>
              <form onSubmit={handleWeatherSubmit} className="stack">
                <label className="field">
                  <span>City</span>
                  <input
                    type="text"
                    value={weatherForm.city}
                    onChange={(event) =>
                      setWeatherForm((current) => ({ ...current, city: event.target.value }))
                    }
                  />
                </label>
                <label className="field">
                  <span>Unit</span>
                  <select
                    value={weatherForm.unit}
                    onChange={(event) =>
                      setWeatherForm((current) => ({ ...current, unit: event.target.value }))
                    }
                  >
                    <option value="celsius">Celsius</option>
                    <option value="fahrenheit">Fahrenheit</option>
                  </select>
                </label>
                <button className="action-button" disabled={loading.weather}>
                  {loading.weather ? "Loading..." : "Run /weather"}
                </button>
              </form>
              <ResultCard
                title="Weather result"
                result={weatherResult}
                renderSuccess={(data) => <p>{data}</p>}
              />
            </section>

            <section className={panelClass(activePanel, "compare")}>
              <h2>Compare two cities</h2>
              <p className="panel-copy">Use the new direct comparison endpoint without going through the agent.</p>
              <form onSubmit={handleCompareSubmit} className="stack">
                <label className="field">
                  <span>First city</span>
                  <input
                    type="text"
                    value={compareForm.cityA}
                    onChange={(event) =>
                      setCompareForm((current) => ({ ...current, cityA: event.target.value }))
                    }
                  />
                </label>
                <label className="field">
                  <span>Second city</span>
                  <input
                    type="text"
                    value={compareForm.cityB}
                    onChange={(event) =>
                      setCompareForm((current) => ({ ...current, cityB: event.target.value }))
                    }
                  />
                </label>
                <label className="field">
                  <span>Unit</span>
                  <select
                    value={compareForm.unit}
                    onChange={(event) =>
                      setCompareForm((current) => ({ ...current, unit: event.target.value }))
                    }
                  >
                    <option value="celsius">Celsius</option>
                    <option value="fahrenheit">Fahrenheit</option>
                  </select>
                </label>
                <button className="action-button" disabled={loading.compare}>
                  {loading.compare ? "Comparing..." : "Run /compare-weather"}
                </button>
              </form>
              <ResultCard
                title="Comparison result"
                result={compareResult}
                renderSuccess={(data) => <p>{data}</p>}
              />
            </section>

            <section className={panelClass(activePanel, "search")}>
              <h2>Search the web</h2>
              <p className="panel-copy">Query the search endpoint and browse normalized search results.</p>
              <form onSubmit={handleSearchSubmit} className="stack">
                <label className="field">
                  <span>Query</span>
                  <input
                    type="text"
                    value={searchForm.query}
                    onChange={(event) =>
                      setSearchForm((current) => ({ ...current, query: event.target.value }))
                    }
                  />
                </label>
                <label className="field">
                  <span>Max results</span>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={searchForm.maxResults}
                    onChange={(event) =>
                      setSearchForm((current) => ({
                        ...current,
                        maxResults: event.target.value
                      }))
                    }
                  />
                </label>
                <button className="action-button" disabled={loading.search}>
                  {loading.search ? "Searching..." : "Run /search"}
                </button>
              </form>
              <SearchResults results={searchResult} />
            </section>
          </div>
        </section>
      </section>
    </main>
  );
}

function tabClass(activePanel, name) {
  return activePanel === name ? "tab active" : "tab";
}

function panelClass(activePanel, name) {
  return activePanel === name ? "panel visible" : "panel hidden";
}

function ResultCard({ title, result, renderSuccess }) {
  return (
    <div className="result-card">
      <div className="result-header">
        <h3>{title}</h3>
      </div>
      {!result && <p className="result-empty">Run the request to see output here.</p>}
      {result?.type === "error" && <p className="result-error">{result.content}</p>}
      {result?.type === "success" && <div className="result-body">{renderSuccess(result.content)}</div>}
    </div>
  );
}

function AskResultView({ data }) {
  if (!data) {
    return null;
  }

  return (
    <div className="ask-result">
      <div className="result-chip-row">
        <span className="result-chip">{data.mode}</span>
        {data.tool_name && <span className="result-chip secondary">{data.tool_name}</span>}
      </div>
      {data.result && (
        <p className="result-lead">
          {typeof data.result === "string" ? data.result : JSON.stringify(data.result, null, 2)}
        </p>
      )}
      {!data.result && data.content && <p className="result-lead">{data.content}</p>}
      {data.raw_response && (
        <details>
          <summary>Model raw output</summary>
          <pre>{data.raw_response}</pre>
        </details>
      )}
    </div>
  );
}

function SearchResults({ results }) {
  if (!results.length) {
    return (
      <div className="result-card">
        <h3>Search results</h3>
        <p className="result-empty">Run a search to populate this panel.</p>
      </div>
    );
  }

  return (
    <div className="search-list">
      {results.map((result, index) => (
        <article key={`${result.url}-${index}`} className="search-item">
          <p className="search-index">{String(index + 1).padStart(2, "0")}</p>
          <div>
            <h3>{result.title || "Untitled result"}</h3>
            {result.url ? (
              <a href={result.url} target="_blank" rel="noreferrer">
                {result.url}
              </a>
            ) : (
              <p className="result-error">{result.snippet}</p>
            )}
            {result.snippet && <p>{result.snippet}</p>}
          </div>
        </article>
      ))}
    </div>
  );
}

function ToolCatalog({ tools, loading }) {
  if (loading) {
    return <p className="result-empty">Loading tool catalog...</p>;
  }

  if (!tools.length) {
    return <p className="result-empty">No tools were returned by the backend.</p>;
  }

  return (
    <div className="tool-list">
      {tools.map((tool) => (
        <article key={tool.name} className="tool-item">
          <h3>{tool.name}</h3>
          <p>{tool.description}</p>
        </article>
      ))}
    </div>
  );
}

function ModelStatusCard({ modelStatus }) {
  if (!modelStatus) {
    return <p className="result-empty">Checking model backend...</p>;
  }

  const reachable = modelStatus.backend_reachable;
  const available = modelStatus.model_available;

  return (
    <div className="model-status-card">
      <div className="result-chip-row">
        <span className={reachable ? "status-pill status-ok" : "status-pill status-offline"}>
          {reachable ? "backend online" : "backend offline"}
        </span>
        <span className={available ? "status-pill status-ok" : "status-pill status-checking"}>
          {available ? "model ready" : "model missing"}
        </span>
      </div>
      <p className="result-lead">{modelStatus.message}</p>
      <dl className="status-grid">
        <div>
          <dt>Configured model</dt>
          <dd>{modelStatus.configured_model}</dd>
        </div>
        <div>
          <dt>Base URL</dt>
          <dd>{modelStatus.base_url || "unknown"}</dd>
        </div>
      </dl>
    </div>
  );
}

export default App;
