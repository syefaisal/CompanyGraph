# CogniGraph

A Neo4j knowledge graph connecting **People → Products → Customers → Workflows → Decisions**, built from plain-text documents via Claude, and exposed via a REST API, a React UI, and an MCP server.

## Document Ingestion Pipeline

The graph data originates from a plain-text company brief — the kind of document that already exists in any company's wiki or shared drive. A single script converts it into a queryable knowledge graph using Claude as the extraction engine.

```
nexus_corp_brief.md          (source: internal company document)
        │
        │  python doc_to_graph.py
        ▼
  Claude Opus (tool use)      ← structured extraction, no hallucination guard needed
        │                        because tool_choice forces one exact tool call
        │  save_knowledge_graph({ entities: [...], relationships: [...] })
        ▼
  doc_to_graph.py             ← validates schema, builds MERGE Cypher statements
        │
        ▼
  Neo4j (graph.py layer)      ← same driver used by REST API + MCP server
        │
        ▼
  30 nodes · 73 relationships ← queryable via UI, API, or Claude Desktop
```

### How it works

**1. Source document** — [`nexus_corp_brief.md`](nexus_corp_brief.md) is written in natural prose: team bios, product descriptions, customer profiles, workflows, and strategic decisions. No schema required from the author.

**2. Claude extracts structure** — `doc_to_graph.py` sends the full document to Claude Opus with a single tool definition (`save_knowledge_graph`) whose input schema mirrors the Neo4j data model. `tool_choice: {type: "tool"}` forces exactly one structured call — no parsing of free-form text.

**3. Entities and relationships loaded** — The tool's output (a list of typed entities + directed relationships) is written to Neo4j using `MERGE` statements via `graph.py`, the same layer used by the REST API and MCP server.

```bash
# Preview what Claude extracts (no Neo4j writes)
python doc_to_graph.py --dry-run

# Load extracted graph (clears existing data first)
python doc_to_graph.py --clear

# Use your own document
python doc_to_graph.py --file my_company.md --clear
```

### Why this matters

Most knowledge graph demos hand-craft seed data. This pipeline shows the realistic path: **unstructured document → LLM extraction → graph database → natural language query**. The same approach works for org charts, engineering RFCs, sales notes, or any prose-heavy internal document.

## Architecture

![Architecture Diagram](architecture.png)

<details>
<summary>ASCII version</summary>

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser / Claude                         │
└────────────┬───────────────────────────┬────────────────────────┘
             │                           │
             ▼                           ▼
┌────────────────────────┐   ┌───────────────────────────────────┐
│    React + Vite UI     │   │        Claude Desktop / Code      │
│  (TypeScript, port 5174)│   │         MCP Client                │
│                        │   └───────────────┬───────────────────┘
│  ┌──────────────────┐  │                   │ MCP protocol
│  │  Force-directed  │  │                   │ (stdio)
│  │  Graph Canvas    │  │   ┌───────────────▼───────────────────┐
│  │  (react-force-   │  │   │         mcp_server.py             │
│  │   graph-2d)      │  │   │       (FastMCP / Python)          │
│  ├──────────────────┤  │   └───────────────┬───────────────────┘
│  │  Query Chat UI   │  │                   │
│  │  (SSE streaming) │  │                   │
└──────────┬───────────┘                     │
           │ /api proxy                       │
           ▼                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI  (port 8000)                       │
│                          api.py                                 │
│                                                                 │
│   GET  /graph          GET  /nodes/{id}     GET  /search        │
│   GET  /impact/{id}    POST /nodes          POST /query  ──────►│
│   POST /relationships  DELETE /nodes/{id}   GET  /path          │
│                                                    │            │
│                                             Anthropic SDK       │
│                                          (Claude Sonnet, SSE)   │
└──────────────────────────┬──────────────────────────────────────┘
                           │  Python neo4j driver  (bolt://7687)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Neo4j 5.x  (Docker)                         │
│                                                                 │
│   (:Person)  ──[:WORKS_ON]──►  (:Product)                       │
│   (:Product) ──[:USED_BY]───►  (:Customer)                      │
│   (:Decision)──[:AFFECTS]───►  (:Workflow | :Product)           │
│   (:Person)  ──[:OWNS]──────►  (:Workflow)                      │
│                                                                 │
│   30 nodes · 73 relationships                                   │
└─────────────────────────────────────────────────────────────────┘
```

</details>

### Key design decisions

| Concern | Decision |
|---------|----------|
| Graph storage | Neo4j — relationships are first-class, Cypher queries are expressive |
| API layer | FastAPI — async, auto-docs, thin wrapper around `graph.py` |
| LLM integration | Full graph serialized into a **cached system prompt** — no RAG chunking needed at this scale |
| Streaming | SSE (`StreamingResponse`) so the UI renders tokens as they arrive |
| Frontend proxy | Vite `/api` → `localhost:8000` — no CORS config required in dev |
| MCP | Same `graph.py` functions reused — one source of truth for all clients |

## Query Flow

![Query Flow Diagram](query_flow.png)

How a natural language question travels through the system when a user types in the Query tab.

### Step-by-step

**1. User input → Frontend** (`UI/src/components/QueryPage.tsx`)

User hits Enter. The component opens a streaming fetch:
```ts
fetch('/api/query', { method: 'POST', body: JSON.stringify({ question }) })
// response body held open as a ReadableStream
```

**2. Vite proxy** (`vite.config.ts`)

The `/api` prefix is rewritten transparently — no CORS headers needed:
```
/api/query  →  http://localhost:8000/query
```

**3. FastAPI receives `POST /query`** (`api.py`)

Three things happen before the LLM is called:

| Step | Code | What it does |
|------|------|--------------|
| Full graph load | `g.get_full_graph()` | Two Cypher queries — all nodes + all relationships |
| Serialization | `_format_graph(graph)` | Converts every node and edge to a readable text string |
| Keyword search | `g.search_nodes(question)` | `CONTAINS` match on `name`, `description`, `role` fields |

**4. Anthropic SDK call with prompt caching**

```python
async with _anthropic.messages.stream(
    model="claude-sonnet-4-6",
    system=[
        { "text": SYSTEM_PROMPT,  "cache_control": {"type": "ephemeral"} },  # cached
        { "text": graph_context,  "cache_control": {"type": "ephemeral"} },  # cached
    ],
    messages=[{ "role": "user", "content": f"{search_hits}\n\nQuestion: {question}" }]
)
```

The two system blocks are marked `ephemeral` — Anthropic caches them for 5 minutes. The first query in a session pays full token cost; every subsequent query hits the cache and costs ~10× less for input tokens. The user message is never cached (unique per query).

**5. SSE stream back to browser** (`api.py`)

Tokens are forwarded to the client the moment they arrive:
```python
async for text in stream.text_stream:
    yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"
yield f"data: {json.dumps({'type': 'done'})}\n\n"
```

**6. Frontend renders tokens as they arrive** (`QueryPage.tsx`)

```ts
const event = JSON.parse(line.slice(6))   // strip "data: "
if (event.type === 'text') {
    // append token → React re-renders → text appears word by word
}
if (event.type === 'done') {
    // set streaming: false → blinking cursor disappears
}
```

### End-to-end diagram

```
QueryPage.tsx
    │  POST /api/query  { question }
    ▼
Vite proxy  →  rewrites to http://localhost:8000/query
    ▼
FastAPI  POST /query
    ├─► Neo4j:  MATCH (n) RETURN n
    │           MATCH (a)-[r]->(b) RETURN type, from_id, to_id   (~5–20 ms)
    │           MATCH (n) WHERE name CONTAINS kw  (keyword search)
    │
    ├─► _format_graph()  →  plain-text representation of all nodes + edges
    │
    └─► AsyncAnthropic.messages.stream()
            system[0]: analyst instructions   ← CACHED (5 min TTL)
            system[1]: full graph text        ← CACHED (5 min TTL)
            user:      search hits + question   (not cached)
                │
                │  token stream
                ▼
        StreamingResponse  media_type="text/event-stream"
                │
                │  data: {"type":"text","content":"Who…"}\n\n
                │  data: {"type":"text","content":" works…"}\n\n
                │  data: {"type":"done"}\n\n
                ▼
        res.body.getReader()  in browser
                │
                ▼
        setMessages(prev → append token)  →  re-render per token
```

### Latency breakdown

| Phase | Typical time |
|-------|-------------|
| Neo4j queries | 5 – 20 ms |
| Graph serialization | < 1 ms |
| Keyword search | 5 – 15 ms |
| Time to first token (Anthropic) | 300 – 800 ms |
| Streaming throughput | ~50 – 80 tokens / sec |

## Stack

| Layer | Tech |
|-------|------|
| Graph DB | Neo4j 5.x (Docker) |
| API | FastAPI (Python) |
| LLM | Claude Sonnet via Anthropic SDK |
| UI | React 18 + Vite + TypeScript + Tailwind |
| Graph viz | react-force-graph-2d (D3 canvas) |
| MCP Server | `mcp` Python SDK (FastMCP) |
| Graph data | Extracted from `nexus_corp_brief.md` via `doc_to_graph.py` + Claude |

## Quickstart

### 1. Install dependencies

```bash
cd /Users/syefai/workspace/CompanyGraph
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Neo4j

```bash
docker compose up -d
# Wait ~15s for Neo4j to be ready
```

Neo4j browser: http://localhost:7474 (neo4j / companygraph123)

### 3. Seed + run the API

```bash
python api.py
# Automatically seeds the graph on first run, then serves at http://localhost:8000
```

Or seed separately:

```bash
python seed.py           # fast static seed (no API key needed)
uvicorn api:app --reload
```

Or extract the graph from the source document using Claude:

```bash
python doc_to_graph.py --clear   # document → Claude extraction → Neo4j
uvicorn api:app --reload
```

API docs: http://localhost:8000/docs

### 4. Use the MCP server with Claude Code

The `.mcp.json` file in this directory auto-registers the MCP server when you open Claude Code here. Claude will have access to these tools:

| Tool | What it does |
|------|-------------|
| `get_graph_summary` | High-level overview of the graph |
| `list_entities` | List all People / Products / Customers / Workflows / Decisions |
| `get_entity` | Get an entity's details + all connections |
| `search_graph` | Full-text search across the graph |
| `find_path` | Shortest path between any two entities |
| `trace_decision_impact` | What does a decision affect (up to 3 hops)? |
| `get_workflow_team` | Who owns / is involved in a workflow? |
| `get_customer_products` | What products does a customer use + who built them? |
| `add_entity` | Add a new entity to the graph |
| `connect_entities` | Create a relationship between two entities |
| `run_cypher` | Execute raw Cypher for advanced queries |

### 5. Claude Desktop config (optional)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "company-graph": {
      "command": "python",
      "args": ["/Users/syefai/workspace/CompanyGraph/mcp_server.py"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "companygraph123"
      }
    }
  }
}
```

## Graph schema

```
(Person)-[:WORKS_ON]-------->(Product)
(Person)-[:OWNS]------------>( Workflow)
(Person)-[:MADE]------------>( Decision)
(Workflow)-[:INVOLVES]------>( Person)
(Workflow)-[:PRODUCES]------>( Product)
(Workflow)-[:DEPENDS_ON]---->( Workflow)
(Customer)-[:USES]---------->( Product)
(Decision)-[:AFFECTS]------->( Product | Customer | Workflow)
```

## Seed data overview

**Nexus Corp** — fictional B2B SaaS company

- 8 people: Sarah Chen (CEO), Marcus Rivera (CTO), Priya Patel (VP Product), Alex Kim, Jordan Lee, Diana Santos, Tom Mitchell, Aisha Okafor
- 4 products: Nexus Analytics, Nexus API Platform, Nexus Connect (beta), Nexus Mobile (deprecated)
- 5 customers: TechFlow Inc, RetailPro Corp, HealthFirst, StartupX, GlobalShip Ltd
- 6 workflows: Customer Onboarding, Sales Pipeline, Bug Triage, Feature Release, Data Migration, Quarterly Planning
- 6 decisions: Deprecate Mobile, Enter Healthcare, Migrate to K8s, Freemium Tier, GDPR Overhaul, DataVault Partnership

## Example Claude queries (via MCP)

> "Who is involved in the Feature Release workflow?"  
> "Trace the impact of the decision to introduce a freemium tier."  
> "Find the connection between Sarah Chen and StartupX."  
> "Which products does our largest customer use and who built them?"  
> "Add a new engineer named 'Mei Zhang' and connect her to the API Platform."
