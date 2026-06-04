"""
Shared pytest configuration and fixtures.

Markers:
  llm         — tests that call the Claude API (slow, cost money).
                Skip with:  pytest -m "not llm"
  integration — tests that need Neo4j or the HTTP API running.
                Skip with:  pytest -m "not integration"

Environment variables:
  API_BASE_URL   override API base (default http://localhost:8000)
"""
import os
import pytest
import httpx

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def pytest_configure(config):
    config.addinivalue_line("markers", "llm: calls the Claude API — skip with -m 'not llm'")
    config.addinivalue_line("markers", "integration: requires Neo4j + API running")


# ── Availability guards ───────────────────────────────────────────────────────

def _neo4j_up() -> bool:
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
        import graph as g
        g.graph_stats()
        return True
    except Exception:
        return False


def _api_up() -> bool:
    try:
        r = httpx.get(f"{API_BASE}/", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# Evaluate once per session
NEO4J_AVAILABLE = _neo4j_up()
API_AVAILABLE = _api_up()


# ── Session-scoped fixtures ───────────────────────────────────────────────────

@pytest.fixture(scope="session")
def api_base():
    return API_BASE


@pytest.fixture(scope="session")
def http():
    """Synchronous httpx client pointed at the running API."""
    with httpx.Client(base_url=API_BASE, timeout=90.0) as client:
        yield client


# ── SSE helper available to all test modules ─────────────────────────────────

def collect_sse(client: httpx.Client, path: str, payload: dict) -> dict:
    """
    POST to an SSE endpoint; collect all events.
    Returns {"text": str, "model": str, "latency_ms": int,
             "tool_calls": int, "events": list[dict]}
    """
    import json

    full_text = ""
    model = "unknown"
    latency_ms = 0
    tool_call_count = 0
    all_events: list[dict] = []

    with client.stream("POST", path, json=payload) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line.startswith("data: "):
                continue
            try:
                event = json.loads(line[6:])
            except Exception:
                continue
            all_events.append(event)
            t = event.get("type")
            if t == "text":
                full_text += event.get("content", "")
            elif t == "tool_call":
                tool_call_count += 1
            elif t == "done":
                model = event.get("model", "unknown")
                latency_ms = event.get("latency_ms", 0)
                tool_call_count = event.get("tool_calls", tool_call_count)

    return {
        "text": full_text,
        "model": model,
        "latency_ms": latency_ms,
        "tool_calls": tool_call_count,
        "events": all_events,
    }


@pytest.fixture
def sse(http):
    """Bound SSE helper using the session HTTP client."""
    def _call(path, payload):
        return collect_sse(http, path, payload)
    return _call
