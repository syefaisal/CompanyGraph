import os
import json
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel
from anthropic import AsyncAnthropic
from models import NodeCreate, RelationshipCreate
import graph as g
# Stateless helpers (prompt loading, graph serialization, input/output safety)
from utils import (
    _load_prompts,
    _format_graph,
    _check_injection,
    _scan_output,
    MAX_QUESTION_LENGTH,
)

# ── LangSmith tracing (optional) ─────────────────────────────────────────────
# Set LANGSMITH_API_KEY + LANGSMITH_TRACING_V2=true in .env to enable.
# All @traceable functions and wrap_anthropic calls become no-ops without it.
from langsmith import traceable
from langsmith.wrappers import wrap_anthropic

_anthropic = wrap_anthropic(AsyncAnthropic())

# ── Prompt versioning ─────────────────────────────────────────────────────────
# Active version is controlled by PROMPT_VERSION in .env (default: v1).
# To create a new version: copy prompts/v1.yaml → prompts/v2.yaml, edit, then
# set PROMPT_VERSION=v2 in .env and restart. Rollback = revert PROMPT_VERSION.
# _load_prompts lives in utils.py.
_PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1")
_prompt_data = _load_prompts(_PROMPT_VERSION)
SYSTEM_PROMPT: str = _prompt_data["prompts"]["system_prompt"].strip()
AGENT_SYSTEM_PROMPT: str = _prompt_data["prompts"]["agent_system_prompt"].strip()
# Multi-agent orchestration prompts — fall back to existing prompts if a prompt
# version predates them, so older YAML files keep working.
PLANNER_SYSTEM_PROMPT: str = _prompt_data["prompts"].get("planner_system_prompt", AGENT_SYSTEM_PROMPT).strip()
WORKER_SYSTEM_PROMPT: str = _prompt_data["prompts"].get("worker_system_prompt", AGENT_SYSTEM_PROMPT).strip()
SYNTHESIZER_SYSTEM_PROMPT: str = _prompt_data["prompts"].get("synthesizer_system_prompt", SYSTEM_PROMPT).strip()

# ── Observability ─────────────────────────────────────────────────────────────

# Daily cost limit — all queries route to Haiku once exceeded.
# Override via DAILY_COST_LIMIT_USD in .env. Set to 0 to disable enforcement.
_DAILY_COST_LIMIT_USD: float = float(os.getenv("DAILY_COST_LIMIT_USD", "5.0"))

_metrics: dict = {
    "query_count": 0,
    "agent_query_count": 0,
    "orchestrate_query_count": 0,
    "direct_query_count": 0,
    "total_latency_ms": 0.0,
    "total_input_tokens": 0,
    "total_cached_tokens": 0,
    "total_output_tokens": 0,
    "cache_hits": 0,
    "errors": 0,
    "safety_events": 0,        # input injection blocks
    "output_safety_events": 0, # output PII detections
    # ── Cost budget ──────────────────────────────────────────────────────────
    "running_cost_usd": 0.0,           # live session total (updated per query)
    "budget_limit_usd": _DAILY_COST_LIMIT_USD,
    "budget_exceeded": False,          # True → all queries forced to Haiku
    "budget_exceeded_at_usd": None,    # cost at the moment the limit was hit
    "model_routes": {
        "direct": 0,
        "claude-haiku-4-5-20251001": 0,
        "claude-sonnet-4-6": 0,
    },
}


import logging as _logging

def _update_metrics(query_type: str, latency_ms: float, usage=None, model: str = "") -> None:
    if query_type == "standard":
        _metrics["query_count"] += 1
    elif query_type == "agent":
        _metrics["agent_query_count"] += 1
    elif query_type == "orchestrate":
        _metrics["orchestrate_query_count"] += 1
    elif query_type == "direct":
        _metrics["direct_query_count"] += 1
    _metrics["total_latency_ms"] += latency_ms
    if usage is not None:
        _metrics["total_input_tokens"] += getattr(usage, "input_tokens", 0)
        cached = getattr(usage, "cache_read_input_tokens", 0) or 0
        _metrics["total_cached_tokens"] += cached
        if cached > 0:
            _metrics["cache_hits"] += 1
        _metrics["total_output_tokens"] += getattr(usage, "output_tokens", 0)
    if model in _metrics["model_routes"]:
        _metrics["model_routes"][model] += 1

    # ── Cost budget enforcement ───────────────────────────────────────────────
    # Conservative estimate using Sonnet pricing (overestimates Haiku cost,
    # which is the safe direction for a budget guard).
    t_in = _metrics["total_input_tokens"]
    t_ca = _metrics["total_cached_tokens"]
    t_ou = _metrics["total_output_tokens"]
    running = ((t_in - t_ca) * 3 + t_ca * 0.30 + t_ou * 15) / 1_000_000
    _metrics["running_cost_usd"] = round(running, 6)

    limit = _DAILY_COST_LIMIT_USD
    if limit > 0 and not _metrics["budget_exceeded"] and running >= limit:
        _metrics["budget_exceeded"] = True
        _metrics["budget_exceeded_at_usd"] = round(running, 6)
        _logging.warning(
            "CogniGraph budget alert: session cost $%.4f reached daily limit $%.2f. "
            "All queries will route to claude-haiku-4-5-20251001 until "
            "POST /admin/reset-budget is called.",
            running, limit,
        )


# ── Safety ────────────────────────────────────────────────────────────────────
# Input prompt-injection defence (_check_injection, MAX_QUESTION_LENGTH) and
# output PII scanning (_scan_output) live in utils.py. Endpoints call them and
# record _metrics["safety_events"] / _metrics["output_safety_events"] on a hit.


# ── Model routing ─────────────────────────────────────────────────────────────

_COMPLEX_INDICATORS = {
    "impact", "affect", "chain", "path", "risk", "depend",
    "connect", "trace", "why", "workflow", "decision",
    "single point", "blast radius", "orphan", "relate",
    "all customers", "all products", "everyone", "compliance",
}


@traceable(name="route_query", run_type="chain",
           metadata={"system": "cogni-graph", "domain": "proptech"})
def route_query(question: str) -> str:
    """Route to haiku for simple entity lookups, sonnet for multi-hop reasoning.
    When the daily cost budget is exceeded, forces all queries to haiku."""
    if _metrics["budget_exceeded"]:
        return "claude-haiku-4-5-20251001"   # cost control override
    q = question.lower()
    if any(ind in q for ind in _COMPLEX_INDICATORS) or len(q.split()) > 12:
        return "claude-sonnet-4-6"
    return "claude-haiku-4-5-20251001"


def _route_explanation(question: str) -> str:
    """Return a short human-readable reason for the routing decision."""
    if _metrics["budget_exceeded"]:
        return "budget limit reached"
    q = question.lower()
    for ind in _COMPLEX_INDICATORS:
        if ind in q:
            return f"'{ind}' detected"
    words = q.split()
    if len(words) > 12:
        return f"{len(words)} words > 12"
    return "simple lookup"


def _try_direct_answer(question: str) -> Optional[str]:
    """Answer simple list/count queries directly from Neo4j — no LLM needed."""
    q = question.lower().strip()
    label_map = {
        "people": "Person", "persons": "Person", "person": "Person",
        "products": "Product", "product": "Product",
        "customers": "Customer", "customer": "Customer",
        "workflows": "Workflow", "workflow": "Workflow",
        "decisions": "Decision", "decision": "Decision",
    }
    if any(kw in q for kw in ("how many", "count of", "number of")):
        stats = g.graph_stats()
        for word, neo_label in label_map.items():
            if word in q:
                count = stats["nodes"].get(neo_label, 0)
                return f"There are {count} {neo_label} nodes in the knowledge graph."
    if q.startswith(("list all", "show all")):
        for word, neo_label in label_map.items():
            if word in q:
                nodes = g.list_nodes(label=neo_label)
                lines = [f"**{neo_label}s** ({len(nodes)} total):"]
                lines += [f"- {n.get('name', n['id'])}" for n in nodes]
                return "\n".join(lines)
    return None


# ── Agent tool definitions ────────────────────────────────────────────────────

AGENT_TOOLS = [
    {
        "name": "search_graph",
        "description": (
            "Search for entities by keyword across name, description, role, category, and industry. "
            "Use this first to find entity IDs before calling get_entity or find_path."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Search term"},
                "entity_type": {
                    "type": "string",
                    "description": "Optional filter: Person, Product, Customer, Workflow, or Decision",
                },
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "get_entity",
        "description": "Get full details and all connections for an entity by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID, e.g. p1, pr2, c3, w4, d5",
                }
            },
            "required": ["entity_id"],
        },
    },
    {
        "name": "find_path",
        "description": "Find the shortest connection path between two entities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_id": {"type": "string"},
                "to_id": {"type": "string"},
            },
            "required": ["from_id", "to_id"],
        },
    },
    {
        "name": "trace_decision_impact",
        "description": (
            "Trace all entities a decision directly or indirectly affects — "
            "products, customers, workflows, and people up to 3 hops away."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "decision_id": {"type": "string", "description": "Decision ID, e.g. d1"}
            },
            "required": ["decision_id"],
        },
    },
    {
        "name": "run_cypher",
        "description": "Execute a Cypher query for advanced analysis not covered by other tools. Read-only recommended.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]

_VALID_ENTITY_TYPES = {"Person", "Product", "Customer", "Workflow", "Decision"}


@traceable(name="execute_graph_tool", run_type="tool",
           metadata={"system": "cogni-graph", "domain": "proptech"})
def _execute_agent_tool(name: str, inputs: dict) -> str:
    if name == "search_graph":
        et = inputs.get("entity_type", "")
        label = et if et in _VALID_ENTITY_TYPES else None
        results = g.hybrid_search_nodes(inputs.get("keyword", ""), label)
        if not results:
            return f"No results for '{inputs.get('keyword', '')}'"
        return json.dumps(
            [{k: v for k, v in n.items() if k not in ("_labels", "_match")} for n in results[:10]],
            default=str,
        )
    if name == "get_entity":
        node = g.get_node_with_connections(inputs["entity_id"])
        if not node:
            return f"No entity found with id '{inputs['entity_id']}'"
        return json.dumps(node, default=str)
    if name == "find_path":
        path = g.find_shortest_path(inputs["from_id"], inputs["to_id"])
        if path is None:
            return f"No path found between '{inputs['from_id']}' and '{inputs['to_id']}'"
        return json.dumps(path, default=str)
    if name == "trace_decision_impact":
        did = inputs["decision_id"]
        node = g.get_node(did)
        rows = g.run(
            "MATCH (d:Decision {id: $id})-[r*1..3]-(m) WHERE m.id <> $id "
            "RETURN DISTINCT labels(m)[0] AS label, m.id AS id, m.name AS name, "
            "min(size(r)) AS hops ORDER BY hops, label",
            {"id": did},
        )
        return json.dumps(
            {"decision": node.get("name") if node else "?", "impact_chain": rows},
            default=str,
        )
    if name == "run_cypher":
        try:
            rows = g.run(inputs["query"])
            return json.dumps(rows[:50], default=str)
        except Exception as exc:
            return f"Cypher error: {exc}"
    return f"Unknown tool: {name}"


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title="Meridian Property Group — Knowledge Graph API", version="2.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/")
def health():
    return {
        "status": "ok",
        "stats": g.graph_stats(),
        "prompt_version": _PROMPT_VERSION,
    }


@app.get("/metrics")
def get_metrics():
    """Observability: query counts, latency, token costs, cache hit rate, model routing distribution."""
    total_queries = (
        _metrics["query_count"]
        + _metrics["agent_query_count"]
        + _metrics["orchestrate_query_count"]
        + _metrics["direct_query_count"]
    )
    total_input = _metrics["total_input_tokens"]
    cached = _metrics["total_cached_tokens"]
    output = _metrics["total_output_tokens"]
    # Approximate Anthropic pricing: Sonnet input $3/1M, cached $0.30/1M, output $15/1M
    cost_usd = ((total_input - cached) * 3 + cached * 0.30 + output * 15) / 1_000_000
    return {
        "prompt_version": _PROMPT_VERSION,
        "prompt_created": _prompt_data.get("created", "unknown"),
        "prompt_description": _prompt_data.get("description", ""),
        "queries": {
            "total": total_queries,
            "standard": _metrics["query_count"],
            "agent": _metrics["agent_query_count"],
            "multi_agent": _metrics["orchestrate_query_count"],
            "direct_no_llm": _metrics["direct_query_count"],
        },
        "latency": {
            "avg_ms": round(_metrics["total_latency_ms"] / max(total_queries, 1), 1),
            "total_ms": round(_metrics["total_latency_ms"], 1),
        },
        "tokens": {
            "input": total_input,
            "cached": cached,
            "output": output,
            "cache_hit_rate": round(cached / max(total_input, 1), 3),
        },
        "cost_usd": round(cost_usd, 4),
        "model_routes": _metrics["model_routes"],
        "cache_hits": _metrics["cache_hits"],
        "errors": _metrics["errors"],
        "safety_events": _metrics["safety_events"],
        "output_safety_events": _metrics["output_safety_events"],
        "budget": {
            "limit_usd": _metrics["budget_limit_usd"],
            "running_cost_usd": _metrics["running_cost_usd"],
            "exceeded": _metrics["budget_exceeded"],
            "exceeded_at_usd": _metrics["budget_exceeded_at_usd"],
            "note": (
                "All queries forced to claude-haiku-4-5-20251001. "
                "Call POST /admin/reset-budget to restore normal routing."
                if _metrics["budget_exceeded"] else
                f"${_metrics['running_cost_usd']:.4f} of ${_metrics['budget_limit_usd']:.2f} used"
            ),
        },
    }


@app.get("/langsmith/runs")
def get_langsmith_runs(limit: int = Query(10, ge=1, le=50)):
    """Return recent LangSmith runs for the cogni-graph project.
    Returns {enabled: false} when LANGSMITH_API_KEY is not set."""
    if not os.getenv("LANGSMITH_API_KEY"):
        return {"enabled": False, "runs": [], "project": None}
    try:
        from langsmith import Client as _LSClient
        ls = _LSClient()
        project = os.getenv("LANGSMITH_PROJECT", "cogni-graph")
        raw = list(ls.list_runs(project_name=project, limit=limit))
        runs = []
        for r in raw:
            latency = None
            if r.end_time and r.start_time:
                latency = round((r.end_time - r.start_time).total_seconds(), 2)
            runs.append({
                "id": str(r.id),
                "name": r.name or "",
                "run_type": r.run_type or "",
                "status": r.status or "",
                "latency_s": latency,
                "input_tokens": getattr(r, "prompt_tokens", None),
                "output_tokens": getattr(r, "completion_tokens", None),
                "start_time": r.start_time.isoformat() if r.start_time else None,
            })
        return {"enabled": True, "project": project, "runs": runs}
    except Exception as exc:
        return {"enabled": True, "error": str(exc), "runs": []}


@app.post("/admin/reset-budget")
def reset_budget():
    """Reset the daily cost budget flag. Normal model routing resumes immediately.
    Token counts are not reset — the running cost continues to accumulate."""
    was_exceeded = _metrics["budget_exceeded"]
    _metrics["budget_exceeded"] = False
    _metrics["budget_exceeded_at_usd"] = None
    _logging.info("CogniGraph: budget flag reset. Normal routing restored.")
    return {
        "reset": True,
        "was_exceeded": was_exceeded,
        "running_cost_usd": _metrics["running_cost_usd"],
        "budget_limit_usd": _metrics["budget_limit_usd"],
    }


@app.get("/graph")
def full_graph():
    return g.get_full_graph()


@app.get("/brief", response_class=PlainTextResponse)
def get_brief():
    path = Path(__file__).parent / "nexus_corp_brief.md"
    if not path.exists():
        raise HTTPException(404, "Brief document not found")
    return path.read_text(encoding="utf-8")


@app.get("/nodes")
def list_nodes(
    type: str = Query(None, description="Filter by label: Person, Product, Customer, Workflow, Decision"),
    limit: int = Query(100, ge=1, le=500),
):
    return g.list_nodes(label=type, limit=limit)


@app.get("/nodes/{node_id}")
def get_node(node_id: str):
    node = g.get_node_with_connections(node_id)
    if not node:
        raise HTTPException(404, f"Node '{node_id}' not found")
    return node


@app.post("/nodes", status_code=201)
def create_node(body: NodeCreate):
    if not body.properties.get("name"):
        raise HTTPException(422, "properties.name is required")
    return g.create_node(body.label, body.properties)


@app.delete("/nodes/{node_id}")
def delete_node(node_id: str):
    if not g.delete_node(node_id):
        raise HTTPException(404, f"Node '{node_id}' not found")
    return {"deleted": node_id}


@app.post("/relationships", status_code=201)
def create_relationship(body: RelationshipCreate):
    ok = g.create_relationship(body.from_id, body.to_id, body.rel_type, body.properties)
    if not ok:
        raise HTTPException(404, "One or both node IDs not found")
    return {"created": True, "from": body.from_id, "to": body.to_id, "type": body.rel_type}


@app.get("/search")
def search(
    q: str = Query(..., min_length=1),
    type: str = Query(None),
    mode: str = Query("hybrid", description="hybrid (BM25 + semantic embeddings via RRF) or keyword (substring)"),
):
    if mode == "hybrid":
        return g.hybrid_search_nodes(q, label=type)
    return g.search_nodes(keyword=q, label=type)


@app.get("/path")
def find_path(from_id: str, to_id: str):
    path = g.find_shortest_path(from_id, to_id)
    if path is None:
        raise HTTPException(404, f"No path found between '{from_id}' and '{to_id}'")
    return {"path": path, "length": len([s for s in path if "node" in s]) - 1}


@app.get("/impact/{node_id}")
def get_impact(node_id: str):
    node = g.get_node(node_id)
    if not node:
        raise HTTPException(404, f"Node '{node_id}' not found")
    rows = g.run(
        "MATCH (n {id: $id})-[r*1..3]-(m) WHERE m.id <> $id "
        "RETURN DISTINCT m, size(r) AS hops ORDER BY hops",
        {"id": node_id},
    )
    return {
        "source": node,
        "reachable": [{"node": g.node_dict(r["m"]), "hops": r["hops"]} for r in rows],
    }


# ── Query models ──────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str


# _format_graph lives in utils.py.


# ── Standard query (full-graph context + prompt caching) ─────────────────────

@app.post("/query")
async def query_graph(body: QueryRequest):
    """Standard query: full graph serialized into a cached system prompt."""
    if not body.question.strip():
        raise HTTPException(422, "question must not be empty")

    violation = _check_injection(body.question)
    if violation:
        _metrics["safety_events"] += 1
        raise HTTPException(400, f"Question rejected by safety filter: {violation}")

    t_start = time.time()

    # Direct answer — skip the LLM entirely for simple list/count queries
    direct = _try_direct_answer(body.question)
    if direct:
        latency = (time.time() - t_start) * 1000
        _update_metrics("direct", latency, model="direct")

        async def _direct_stream():
            yield f"data: {json.dumps({'type': 'text', 'content': direct})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'model': 'direct', 'route_reason': 'direct answer — no LLM', 'latency_ms': round(latency)})}\n\n"

        return StreamingResponse(
            _direct_stream(),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    model = route_query(body.question)
    graph = g.get_full_graph()
    graph_context = _format_graph(graph)
    search_hits = g.hybrid_search_nodes(body.question)
    search_text = (
        "Hybrid BM25 search results:\n"
        + "\n".join(f"- [{h['label']}] {h.get('name', h['id'])}" for h in search_hits)
        if search_hits
        else "No direct keyword matches found."
    )

    async def event_stream():
        final_usage = None
        try:
            # Buffer the full response so _scan_output() can check complete
            # token sequences (a card number may span multiple stream chunks).
            full_text = ""
            async with _anthropic.messages.stream(
                model=model,
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": f"Full knowledge graph:\n\n{graph_context}",
                        "cache_control": {"type": "ephemeral"},
                    },
                ],
                messages=[
                    {
                        "role": "user",
                        "content": f"{search_text}\n\nQuestion: {body.question}",
                    }
                ],
            ) as stream:
                async for text in stream.text_stream:
                    full_text += text
                final_message = await stream.get_final_message()
                final_usage = final_message.usage

            # Scan buffered output for PII before sending to the browser
            safe_text, violations = _scan_output(full_text)
            if violations:
                _metrics["output_safety_events"] += 1
                yield f"data: {json.dumps({'type': 'safety_warning', 'violations': violations})}\n\n"

            # Emit the (possibly redacted) text in chunks
            for i in range(0, len(safe_text), 80):
                yield f"data: {json.dumps({'type': 'text', 'content': safe_text[i:i+80]})}\n\n"

            latency = (time.time() - t_start) * 1000
            _update_metrics("standard", latency, final_usage, model)
            yield f"data: {json.dumps({'type': 'done', 'model': model, 'route_reason': _route_explanation(body.question), 'latency_ms': round(latency)})}\n\n"
        except Exception as exc:
            _metrics["errors"] += 1
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


# ── Agentic query (iterative tool-calling loop) ───────────────────────────────

@traceable(name="agent_query", run_type="chain",
           metadata={"system": "cogni-graph", "domain": "proptech", "endpoint": "/query/agent"})
async def _run_agent_traced(question: str, model: str) -> dict:
    """
    Traced wrapper for the full agent execution (non-streaming).
    Called in the background so LangSmith captures the complete run tree:
      agent_query (chain)
        └─ route_query        (chain)   — routing decision
        └─ messages.create    (llm)     — each LLM turn, auto-traced by wrap_anthropic
        └─ execute_graph_tool (tool)    — each tool call
    Returns {"answer": str, "tool_calls": int} for LangSmith output capture.
    """
    messages: list[dict] = [{"role": "user", "content": question}]
    tool_call_count = 0
    final_text = ""

    for _ in range(8):
        response = await _anthropic.messages.create(
            model=model,
            max_tokens=4096,
            system=AGENT_SYSTEM_PROMPT,
            tools=AGENT_TOOLS,
            messages=messages,
        )
        if response.stop_reason == "tool_use":
            assistant_content: list[dict] = []
            tool_results: list[dict] = []
            for block in response.content:
                if block.type == "text" and block.text:
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    tool_call_count += 1
                    result = _execute_agent_tool(block.name, block.input)
                    assistant_content.append(
                        {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
                    )
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": result}
                    )
            messages = messages + [
                {"role": "assistant", "content": assistant_content},
                {"role": "user", "content": tool_results},
            ]
        elif response.stop_reason == "end_turn":
            final_text = "".join(b.text for b in response.content if hasattr(b, "text"))
            break

    return {"answer": final_text, "tool_calls": tool_call_count, "model": model}


@app.post("/query/agent")
async def query_graph_agent(body: QueryRequest):
    """
    Agentic query mode: Claude iteratively calls graph tools to answer questions.

    SSE event types:
      thinking    — Claude's intermediate reasoning text before tool calls
      tool_call   — tool name + input chosen by Claude
      tool_result — truncated result returned to Claude
      text        — final answer tokens
      done        — completion with tool_calls count and latency_ms
    """
    if not body.question.strip():
        raise HTTPException(422, "question must not be empty")

    violation = _check_injection(body.question)
    if violation:
        _metrics["safety_events"] += 1
        raise HTTPException(400, f"Question rejected by safety filter: {violation}")

    t_start = time.time()
    model = route_query(body.question)
    messages: list[dict] = [{"role": "user", "content": body.question}]
    total_input_tokens = 0
    total_output_tokens = 0

    # Fire the traced run in the background so LangSmith captures the full
    # agent execution tree (chain → llm turns → tool calls) independently
    # of the SSE stream that delivers tokens to the browser.
    import asyncio
    if os.getenv("LANGSMITH_TRACING_V2"):
        asyncio.ensure_future(_run_agent_traced(body.question, model))

    async def agent_stream():
        nonlocal messages, total_input_tokens, total_output_tokens
        tool_call_count = 0
        max_iterations = 8

        for _ in range(max_iterations):
            try:
                response = await _anthropic.messages.create(
                    model=model,
                    max_tokens=4096,
                    system=AGENT_SYSTEM_PROMPT,
                    tools=AGENT_TOOLS,
                    messages=messages,
                )
            except Exception as exc:
                _metrics["errors"] += 1
                yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"
                return

            total_input_tokens += getattr(response.usage, "input_tokens", 0)
            total_output_tokens += getattr(response.usage, "output_tokens", 0)

            if response.stop_reason == "tool_use":
                assistant_content: list[dict] = []
                tool_results: list[dict] = []

                for block in response.content:
                    if block.type == "text" and block.text:
                        yield f"data: {json.dumps({'type': 'thinking', 'content': block.text})}\n\n"
                        assistant_content.append({"type": "text", "text": block.text})
                    elif block.type == "tool_use":
                        tool_call_count += 1
                        yield f"data: {json.dumps({'type': 'tool_call', 'tool': block.name, 'input': block.input})}\n\n"

                        result = _execute_agent_tool(block.name, block.input)
                        preview = result[:500] + "…" if len(result) > 500 else result
                        yield f"data: {json.dumps({'type': 'tool_result', 'tool': block.name, 'result': preview})}\n\n"

                        assistant_content.append(
                            {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
                        )
                        tool_results.append(
                            {"type": "tool_result", "tool_use_id": block.id, "content": result}
                        )

                messages = messages + [
                    {"role": "assistant", "content": assistant_content},
                    {"role": "user", "content": tool_results},
                ]

            elif response.stop_reason == "end_turn":
                raw_text = "".join(
                    b.text for b in response.content if hasattr(b, "text")
                )
                # Scan for PII before emitting — agent final answer is already
                # fully assembled so we can check the complete text at once.
                final_text, violations = _scan_output(raw_text)
                if violations:
                    _metrics["output_safety_events"] += 1
                    yield f"data: {json.dumps({'type': 'safety_warning', 'violations': violations})}\n\n"

                # Emit in 40-char chunks to simulate streaming for the UI
                for i in range(0, len(final_text), 40):
                    yield f"data: {json.dumps({'type': 'text', 'content': final_text[i:i+40]})}\n\n"

                latency = (time.time() - t_start) * 1000
                _update_metrics("agent", latency, None, model)
                _metrics["total_input_tokens"] += total_input_tokens
                _metrics["total_output_tokens"] += total_output_tokens

                yield f"data: {json.dumps({'type': 'done', 'model': model, 'route_reason': _route_explanation(body.question), 'tool_calls': tool_call_count, 'latency_ms': round(latency)})}\n\n"
                return

            else:
                yield f"data: {json.dumps({'type': 'error', 'content': f'Unexpected stop_reason: {response.stop_reason}'})}\n\n"
                return

        yield f"data: {json.dumps({'type': 'error', 'content': 'Agent reached max iterations (8)'})}\n\n"

    return StreamingResponse(
        agent_stream(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


# ── Multi-agent orchestration (planner → parallel workers → synthesizer) ───────
# Additive endpoint. The standard /query and /query/agent paths are unchanged.
# A planner decomposes the question into independent sub-questions; one worker
# agent (each a bounded tool-calling loop over the same graph tools) researches
# each in parallel; a synthesizer merges the findings into one grounded answer.
# Per-role model routing demonstrates cost control: cheap workers, capable synth.

ORCH_PLANNER_MODEL = os.getenv("ORCH_PLANNER_MODEL", "claude-sonnet-4-6")
ORCH_WORKER_MODEL = os.getenv("ORCH_WORKER_MODEL", "claude-haiku-4-5-20251001")
ORCH_SYNTH_MODEL = os.getenv("ORCH_SYNTH_MODEL", "claude-sonnet-4-6")
ORCH_MAX_SUBTASKS = int(os.getenv("ORCH_MAX_SUBTASKS", "4"))
ORCH_WORKER_MAX_ITERS = 5

PLANNER_TOOL = {
    "name": "submit_plan",
    "description": (
        "Submit the decomposition of the user's question into independent "
        "sub-questions to be researched in parallel."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "subtasks": {
                "type": "array",
                "description": "2 to 4 independent, self-contained sub-questions.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Short id, e.g. s1"},
                        "question": {"type": "string"},
                    },
                    "required": ["question"],
                },
            }
        },
        "required": ["subtasks"],
    },
}


@traceable(name="orchestrate_plan", run_type="chain",
           metadata={"system": "cogni-graph", "domain": "proptech"})
async def _make_plan(question: str, model: str) -> tuple[list[dict], int, int]:
    """Planner agent: decompose the question via a forced submit_plan tool call.
    Returns (subtasks, input_tokens, output_tokens)."""
    resp = await _anthropic.messages.create(
        model=model,
        max_tokens=1024,
        system=PLANNER_SYSTEM_PROMPT,
        tools=[PLANNER_TOOL],
        tool_choice={"type": "tool", "name": "submit_plan"},
        messages=[{"role": "user", "content": question}],
    )
    in_tok = getattr(resp.usage, "input_tokens", 0)
    out_tok = getattr(resp.usage, "output_tokens", 0)
    subtasks: list[dict] = []
    for block in resp.content:
        if block.type == "tool_use" and block.name == "submit_plan":
            raw = block.input.get("subtasks", []) or []
            for i, st in enumerate(raw[:ORCH_MAX_SUBTASKS]):
                q = (st or {}).get("question", "").strip()
                if q:
                    subtasks.append({"id": st.get("id") or f"s{i + 1}", "question": q})
            break
    return subtasks, in_tok, out_tok


@traceable(name="orchestrate_worker", run_type="chain",
           metadata={"system": "cogni-graph", "domain": "proptech"})
async def _run_worker(subtask_id: str, subquestion: str, model: str) -> dict:
    """One worker sub-agent: a bounded tool-calling loop scoped to a single
    sub-question. Returns {id, question, answer, tool_calls, in, out}."""
    messages: list[dict] = [{"role": "user", "content": subquestion}]
    tool_calls = 0
    answer = ""
    in_tok = 0
    out_tok = 0
    for _ in range(ORCH_WORKER_MAX_ITERS):
        resp = await _anthropic.messages.create(
            model=model,
            max_tokens=2048,
            system=WORKER_SYSTEM_PROMPT,
            tools=AGENT_TOOLS,
            messages=messages,
        )
        in_tok += getattr(resp.usage, "input_tokens", 0)
        out_tok += getattr(resp.usage, "output_tokens", 0)
        if resp.stop_reason == "tool_use":
            assistant_content: list[dict] = []
            tool_results: list[dict] = []
            for block in resp.content:
                if block.type == "text" and block.text:
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    tool_calls += 1
                    result = _execute_agent_tool(block.name, block.input)
                    assistant_content.append(
                        {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
                    )
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": result}
                    )
            messages = messages + [
                {"role": "assistant", "content": assistant_content},
                {"role": "user", "content": tool_results},
            ]
        elif resp.stop_reason == "end_turn":
            answer = "".join(b.text for b in resp.content if hasattr(b, "text"))
            break
    return {
        "id": subtask_id, "question": subquestion, "answer": answer,
        "tool_calls": tool_calls, "in": in_tok, "out": out_tok,
    }


@app.post("/query/orchestrate")
async def query_graph_orchestrate(body: QueryRequest):
    """
    Multi-agent query mode: planner → parallel worker sub-agents → synthesizer.

    SSE event types:
      plan            — the decomposed sub-questions + planner model
      subagent_start  — a worker sub-agent began (id, question, model)
      subagent_result — a worker finished (id, answer preview, tool_calls)
      synthesis       — the synthesizer started (model)
      text            — final synthesized answer tokens
      safety_warning  — PII redaction occurred in the final answer
      done            — completion with sub-agent + tool counts, latency, models
    """
    import asyncio

    if not body.question.strip():
        raise HTTPException(422, "question must not be empty")

    violation = _check_injection(body.question)
    if violation:
        _metrics["safety_events"] += 1
        raise HTTPException(400, f"Question rejected by safety filter: {violation}")

    t_start = time.time()

    async def orchestrate_stream():
        total_in = 0
        total_out = 0
        try:
            # 1. Plan
            plan, p_in, p_out = await _make_plan(body.question, ORCH_PLANNER_MODEL)
            total_in += p_in
            total_out += p_out
            if not plan:  # planner returned nothing → degrade to a single sub-agent
                plan = [{"id": "s1", "question": body.question}]
            yield f"data: {json.dumps({'type': 'plan', 'subtasks': plan, 'planner_model': ORCH_PLANNER_MODEL})}\n\n"
            for st in plan:
                yield f"data: {json.dumps({'type': 'subagent_start', 'id': st['id'], 'question': st['question'], 'model': ORCH_WORKER_MODEL})}\n\n"

            # 2. Workers in parallel; emit each result as it completes
            results: list[dict] = []
            coros = [_run_worker(st["id"], st["question"], ORCH_WORKER_MODEL) for st in plan]
            for fut in asyncio.as_completed(coros):
                res = await fut
                total_in += res["in"]
                total_out += res["out"]
                results.append(res)
                preview = res["answer"][:600] + ("…" if len(res["answer"]) > 600 else "")
                yield f"data: {json.dumps({'type': 'subagent_result', 'id': res['id'], 'answer': preview, 'tool_calls': res['tool_calls']})}\n\n"

            # 3. Synthesize (streamed); buffer first so PII scan sees whole tokens
            yield f"data: {json.dumps({'type': 'synthesis', 'model': ORCH_SYNTH_MODEL})}\n\n"
            findings = "\n\n".join(
                f"### Sub-question: {r['question']}\n{r['answer'] or '(no answer)'}"
                for r in sorted(results, key=lambda r: r["id"])
            )
            synth_user = (
                f"Original question: {body.question}\n\n"
                f"Findings from research sub-agents:\n{findings}\n\n"
                "Synthesize a single, coherent answer to the original question, "
                "grounded only in these findings."
            )
            full_text = ""
            async with _anthropic.messages.stream(
                model=ORCH_SYNTH_MODEL,
                max_tokens=2048,
                system=SYNTHESIZER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": synth_user}],
            ) as stream:
                async for text in stream.text_stream:
                    full_text += text
                final_message = await stream.get_final_message()
                total_in += getattr(final_message.usage, "input_tokens", 0)
                total_out += getattr(final_message.usage, "output_tokens", 0)

            safe_text, violations = _scan_output(full_text)
            if violations:
                _metrics["output_safety_events"] += 1
                yield f"data: {json.dumps({'type': 'safety_warning', 'violations': violations})}\n\n"
            for i in range(0, len(safe_text), 80):
                yield f"data: {json.dumps({'type': 'text', 'content': safe_text[i:i + 80]})}\n\n"

            # 4. Metrics (additive) — record one multi-agent query + per-role model calls
            latency = (time.time() - t_start) * 1000
            usage = SimpleNamespace(
                input_tokens=total_in, output_tokens=total_out, cache_read_input_tokens=0
            )
            _update_metrics("orchestrate", latency, usage, model="")
            for m in (ORCH_PLANNER_MODEL, ORCH_SYNTH_MODEL):
                if m in _metrics["model_routes"]:
                    _metrics["model_routes"][m] += 1
            if ORCH_WORKER_MODEL in _metrics["model_routes"]:
                _metrics["model_routes"][ORCH_WORKER_MODEL] += len(plan)

            yield f"data: {json.dumps({'type': 'done', 'model': f'multi-agent · {len(plan)} sub-agents', 'route_reason': f'{len(plan)} parallel sub-agents', 'subtasks': len(plan), 'tool_calls': sum(r['tool_calls'] for r in results), 'latency_ms': round(latency), 'models': {'planner': ORCH_PLANNER_MODEL, 'worker': ORCH_WORKER_MODEL, 'synthesizer': ORCH_SYNTH_MODEL}})}\n\n"
        except Exception as exc:
            _metrics["errors"] += 1
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

    return StreamingResponse(
        orchestrate_stream(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


if __name__ == "__main__":
    import uvicorn
    from seed import seed
    seed()
    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"), port=int(os.getenv("API_PORT", 8000)))
