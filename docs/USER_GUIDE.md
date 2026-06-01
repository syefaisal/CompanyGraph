# CogniGraph — User Guide

## Sample Questions and Architectural Decisions

The six sample questions in the Query tab are each designed to demonstrate a distinct intersection of architectural decisions. This guide explains what each question exercises and why it was chosen.

---

### 👥 "Who owns the Lease Renewal workflow and who else is involved?"

**Model routing → Haiku** — 9 words, no multi-hop complexity keywords. Routes to the cheaper model automatically. Demonstrates the **right-sizing decision** from production AI engineering: model routing, distillation, and caching strategies.

**Graph-native structural query** — ownership and involvement are explicit typed relationships (`OWNS`, `INVOLVES`) in the graph. A vector/RAG system with chunked documents would struggle to answer "who else is involved" reliably because that is structural, not semantic. Demonstrates **knowledge graph over flat RAG** for organizational data.

---

### ⚖️ "Trace the full impact of the GDPR and CCPA compliance overhaul."

**Model routing → Sonnet** — "compliance" is a complexity indicator. Routes up automatically.

**Multi-hop graph traversal** — Decision → Products → Customers → Workflows → People, up to 3 hops. This is the core knowledge graph value proposition: traversing a relationship chain that no single document chunk contains.

**Agentic tool-calling loop** — in `/query/agent` mode, Claude calls `search_graph` → `trace_decision_impact` → `get_entity` in sequence, reasoning across results before answering. Demonstrates the **responder/thinker pattern**: the agent plans, executes tools, observes results, and synthesizes a final answer.

**PropTech domain fit** — GDPR, CCPA, and fair housing compliance are the exact regulatory concerns a PropTech company faces. Shows domain awareness, not just generic AI architecture.

**Observability** — `/metrics` records which model was used, how many tokens were consumed, whether the graph context cache was hit, and the estimated cost of this specific query.

---

### 🔗 "Find the connection between Elena Rodriguez and Apex Commercial."

**Shortest-path graph algorithm** — `shortestPath((a)-[*..10]-(b))` in Cypher. This is a query type that **cannot be answered by vector similarity**. There is no document that contains "Elena Rodriguez is connected to Apex Commercial via Enter Commercial Market decision." The connection only exists as a traversal. Demonstrates **knowledge graph as the right tool for relationship queries** vs. RAG for document retrieval.

**Multi-hop reasoning** — Elena → `MADE` → Enter Commercial Market → `AFFECTS` → Apex Commercial. The path is discovered dynamically, not pre-computed.

**Hybrid BM25 search** — finds both "Elena Rodriguez" and "Apex Commercial" accurately even though the query contains both names, because IDF weighting prevents common words from drowning out specific entity names.

---

### 🏢 "Which products does Sunstone Residential use and who built them?"

**Model routing → Haiku** — 11 words, no complexity indicators. This is the **cost management** story: a factual customer-360 lookup should not spend Sonnet tokens. Demonstrates right-sizing thinking and build-vs-buy tradeoffs.

**Prompt caching payoff** — the full graph is already in the cached system prompt from the previous query. This query's input tokens hit the cache at ~10× lower cost. Demonstrates **semantic caching** from the retrieval architecture layer.

**Cross-entity join** — Customer → `USES` → Products → `WORKS_ON` ← People. Three entity types linked in a single answer. A document-based system would require at least two separate lookups and manual joining.

---

### ⚠️ "What workflows would be at risk if Marcus Webb left the company?"

**Model routing → Sonnet** — "risk" is a complexity indicator, and the question requires counterfactual reasoning (what *would* happen).

**Organizational risk analysis** — finds workflows where Marcus is the sole `OWNS` holder (bus factor = 1), then traces what breaks downstream via `DEPENDS_ON` chains. Demonstrates knowledge graphs for **operational risk**, not just information retrieval.

**Multi-hop dependency chain** — Work Order Processing → Vendor Onboarding → Quarterly Owner Reporting. The risk radiates through the dependency graph. A flat HR document would tell you Marcus's title; the graph tells you the blast radius.

---

### ➕ "Add a new compliance engineer named 'Kai Patel' and connect them to the Fair Housing Audit workflow."

**Agentic write operation** — Claude must call `add_entity` (create Person node) then `connect_entities` (create `INVOLVES` relationship) — two sequential tool calls where the second depends on the ID returned by the first. This is the purest demonstration of the **agentic multi-step tool-calling pattern**: the model plans, executes, and chains actions.

**Live graph update** — after this query runs, Kai Patel immediately appears in the force-directed graph visualization, shows up in search results, and is included in future compliance impact traces. Demonstrates the system as a **living knowledge base**, not a static index.

**Responsible AI / governance angle** — adding someone to a Fair Housing Audit workflow in a property management company has real compliance implications. This question deliberately touches the PropTech regulatory domain to show domain fit for a company where AI decisions have legal weight.

---

## Architecture Decision Matrix

The table below maps each sample question to the JD-aligned architectural capabilities it exercises.

| Capability | 👥 Ownership | ⚖️ Compliance | 🔗 Connection | 🏢 Customer 360 | ⚠️ Risk | ➕ Write |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Model routing (right-sizing) | Haiku | Sonnet | Sonnet | Haiku | Sonnet | Sonnet |
| Agentic tool-calling loop | | ✓ | | | | ✓ |
| Knowledge graph (structural query) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Hybrid BM25 search | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Multi-hop traversal | | ✓ | ✓ | ✓ | ✓ | |
| Prompt caching (cost management) | | | | ✓ | | |
| Shortest-path algorithm | | | ✓ | | | |
| Organizational risk / bus factor | | | | | ✓ | |
| Live graph write + immediate reflection | | | | | | ✓ |
| PropTech / compliance domain | | ✓ | | | ✓ | ✓ |
| Real-time SSE streaming | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Observability via /metrics | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| LangSmith tracing | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| CI/CD quality gate | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Cost budget enforcement | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Prompt injection defence (input) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Output PII scanning & redaction | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Safety guidelines in system prompt | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Routing decision badge (why this model) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Observe tab (live metrics + LangSmith feed) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## Observe Tab — Model Selection Strategy & Live Metrics

The **Observe** tab (fourth tab in the header) is a real-time dashboard that makes the model selection strategy and LangSmith traces visible without leaving the app.

### Routing Decision Badge

Every assistant response in the Query tab shows a colour-coded pill immediately after streaming completes:

| Badge colour | Tier | Trigger | What it means |
|-------------|------|---------|---------------|
| 🟢 Green | **Direct** | List/count questions | Neo4j answered directly — zero LLM cost |
| 🔵 Blue | **Haiku** | Short questions, no complexity keywords | Fast, cheap model for simple lookups |
| 🟣 Violet | **Sonnet** | `compliance`, `impact`, `trace`, >12 words, etc. | Full reasoning model for complex multi-hop queries |

The badge also shows the exact routing reason (e.g. `'compliance' detected`) and elapsed time.

### Observe Tab Sections

**Key Metrics** — four cards refreshed every 10 s:
- Total queries with standard / agent / direct breakdown
- Average latency across all queries
- Session cost (USD) and cache hit rate
- Safety events (input injection blocks + output PII detections)

**Budget Status** — progress bar showing `$X.XX / $5.00` spend. Turns amber when the daily limit is exceeded and shows the reset instruction.

**Model Selection Strategy** — horizontal bar chart per routing tier:
```
Direct  ████░░░░░░░░░░░░░░░░░  28%   List/count queries — zero LLM cost
Haiku   ████████░░░░░░░░░░░░░  38%   Simple entity lookups — fast and cheap
Sonnet  ████████████░░░░░░░░░  34%   Complex multi-hop reasoning
```
Below the bars: token breakdown — input, cached, and output tokens with cache hit rate.

**LangSmith Trace Feed** — table of last 15 runs pulled from the `cogni-graph` project via `GET /langsmith/runs`. Shows run name, type badge (chain/llm/tool), status, latency, and token counts. Updates every 10 s. Shows setup instructions when `LANGSMITH_API_KEY` is absent.

---

## Cost Budget Enforcement

The API enforces a daily cost limit to prevent runaway LLM spend. Configure in `.env`:

```bash
DAILY_COST_LIMIT_USD=5.00   # default — set to 0 to disable
```

### How the limit is enforced

| Step | Where | What happens |
|------|-------|-------------|
| After every query | `_update_metrics()` | Recalculates `running_cost_usd` from token counters |
| Limit reached | `_update_metrics()` | Sets `budget_exceeded = True`, emits a `WARNING` log |
| Next query routing | `route_query()` | Checks flag first — returns `claude-haiku-4-5-20251001` regardless of question complexity |
| Visibility | `GET /metrics` | `"budget"` block shows limit, running cost, exceeded flag, and a human-readable note |
| Recovery | `POST /admin/reset-budget` | Clears the flag immediately — no restart needed |

### /metrics budget block

```json
"budget": {
  "limit_usd": 5.0,
  "running_cost_usd": 5.0124,
  "exceeded": true,
  "exceeded_at_usd": 5.0011,
  "note": "All queries forced to claude-haiku-4-5-20251001. Call POST /admin/reset-budget to restore normal routing."
}
```

### Reset after exceeding

```bash
curl -X POST http://localhost:8000/admin/reset-budget
# → {"reset": true, "was_exceeded": true, "running_cost_usd": 5.01, "budget_limit_usd": 5.0}
```

Normal Sonnet routing resumes on the next query. Running cost continues to accumulate — only the routing override is cleared.

---

## CI/CD Pipeline

Two GitHub Actions workflows enforce quality automatically. No manual test runs required after setup.

### `ci.yml` — Push & PR gate

Triggers on every push to `main` and every pull request. **All jobs must pass before a PR can be merged.**

| Job | What it checks | Services needed |
|-----|---------------|----------------|
| **syntax-and-unit** | `py_compile` on all `.py` files + 48 unit tests | None — runs in ~0.5 s |
| **prompt-validation** | All `backend/prompts/*.yaml` files are valid YAML with required keys | None |
| **integration** | 65 graph tests + 63 API tests (no LLM calls) | Neo4j container (auto-provisioned) |

A dummy Anthropic key is used for the integration job — no real key, no cost.

### `eval-nightly.yml` — Daily quality gate

Runs at 06:00 UTC every day. Can also be triggered manually from the Actions tab.

```
Neo4j → seed → API start → eval.py → regression check
                                           │
                     recall ≥ 0.85 ──────── ✓ upload artifact (90 days)
                     recall < 0.85 ──────── ✗ upload artifact + GitHub issue created
```

**Regression thresholds** (configurable in `scripts/check_eval_regression.py`):

| Check | Must pass |
|-------|-----------|
| Average entity recall | ≥ 0.85 |
| Pass rate (cases) | ≥ 75% — 6 of 8 |
| Zero-recall cases | 0 allowed |

### GitHub Secrets to add

Go to **Settings → Secrets and variables → Actions** in your repository:

| Secret | Used by | Required |
|--------|---------|----------|
| `ANTHROPIC_API_KEY` | `eval-nightly.yml` | Yes — for LLM calls |
| `LANGSMITH_API_KEY` | `eval-nightly.yml` | Optional — for nightly tracing |

### Manual eval trigger

Open **Actions → Nightly Eval → Run workflow** and choose:
- **standard** — evaluates `/query` (default, faster)
- **agent** — evaluates `/query/agent` (more thorough, uses more tokens)

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/validate_prompts.py` | Validates all `backend/prompts/*.yaml` files — called in CI and runnable locally |
| `scripts/check_eval_regression.py` | Reads eval JSON, fails if thresholds breached — called after nightly eval |

```bash
# Run locally at any time
python3 scripts/validate_prompts.py
python3 scripts/check_eval_regression.py backend/eval_results/2026-05-31_18-20_standard.json
```

---

## Output Safety Guardrails

Two layers protect against sensitive data reaching the browser.

### Layer 1 — Safety guidelines in the system prompt (`backend/prompts/v2.yaml`)

The system prompt in `backend/prompts/v2.yaml` explicitly instructs Claude never to reproduce or infer sensitive personal information:

> *"Never generate, reproduce, or infer sensitive personal information. This includes Social Security Numbers, payment card numbers, bank account or routing numbers, and personal contact details outside the organisation. Describe sensitive fields by field name only — do not speculate about or reconstruct actual values."*

This applies to both the standard query prompt and the agent system prompt.

**To activate `v2.yaml`** — add to `.env` and restart the API:
```bash
PROMPT_VERSION=v2
```

### Layer 2 — Output PII scanning (`_scan_output`)

Every LLM response is scanned before any token is sent to the browser. Both `/query` and `/query/agent` buffer the complete response first so patterns spanning multiple stream chunks are caught.

**PII types detected and redacted:**

| Pattern | Example matched | Sent to browser |
|---------|----------------|-----------------|
| `SSN` | `123-45-6789` | `[REDACTED:SSN]` |
| `PAYMENT_CARD` | `4111 1111 1111 1111` (Visa/MC/Amex/Discover) | `[REDACTED:PAYMENT_CARD]` |
| `ROUTING_NUMBER` | `021000021` (9-digit ABA) | `[REDACTED:ROUTING_NUMBER]` |
| `EXTERNAL_EMAIL` | `tenant@gmail.com` | `[REDACTED:EXTERNAL_EMAIL]` |

Internal `@meridianpg.com` addresses are **not** flagged — they are legitimate business contacts already in the knowledge graph.

### SSE safety_warning event

When PII is detected in an output, a `safety_warning` event is emitted to the client before the text events:

```json
{"type": "safety_warning", "violations": ["SSN", "PAYMENT_CARD"]}
```

The UI can use this event to display an inline notice. The `output_safety_events` counter in `GET /metrics` tracks total detections across all queries.

### Test coverage

14 tests in `tests/test_unit_safety.py::TestOutputSafety` verify detection, redaction, and false-positive protection:
- SSN formatted with surrounding text preserved
- Payment card variants (formatted/unformatted, four card types)
- Routing number (ABA format)
- External email detected / internal email not flagged
- MRR, ARR, unit counts, dates, versions confirmed as **not** triggering false positives

---

## LangSmith Tracing

LangSmith provides full distributed tracing for every LLM call, tool execution, and routing decision. It is **optional** — all tracing decorators and wrappers are no-ops when disabled.

> **The master switch is `LANGSMITH_TRACING_V2=true`.** Setting only `LANGSMITH_API_KEY` is not enough — nothing will appear in LangSmith until this flag is explicitly set. The API must also be restarted after any `.env` change, because `dotenv` loads vars once at process start.

### What is traced

| Trace | Mechanism | LangSmith run type | When it fires |
|-------|-----------|--------------------|---------------|
| Query routing decision | `@traceable` on `route_query` | `chain` | Every `/query` and `/query/agent` call |
| Agent-loop LLM call | `wrap_anthropic` patches `messages.create` | `llm` | Each turn of the agent loop |
| Tool execution | `@traceable` on `_execute_agent_tool` | `tool` | Every tool call inside the agent |
| Full agent run tree | `_run_agent_traced()` background task | `chain` (parent) | Every `/query/agent` call |

### Trace tree for an agent query

A single question like *"Trace the GDPR compliance impact"* produces this tree in LangSmith:

```
agent_query (chain)                          ~36 s total
  ├─ route_query (chain)                     → "claude-sonnet-4-6"
  ├─ ChatAnthropic (llm)                     turn 1 — stop: tool_use
  │    inputs:  messages, system, tools
  │    outputs: tool_use blocks
  │    tokens:  input=4,200  output=180
  ├─ execute_graph_tool (tool)               search_graph("GDPR")
  ├─ execute_graph_tool (tool)               trace_decision_impact("d4")
  ├─ execute_graph_tool (tool)               get_entity("pr1") — LeaseTrack
  ├─ execute_graph_tool (tool)               get_entity("pr3") — TenantPay
  ├─ ChatAnthropic (llm)                     turn 5 — stop: end_turn
  │    outputs: final answer text
  │    tokens:  input=6,800  output=920
  └─ [done]
```

Each node shows: inputs, outputs, latency, token counts, and metadata (`domain: proptech`, `system: cogni-graph`).

### Setup

**1. Get a free API key** at [smith.langchain.com](https://smith.langchain.com)

**2. Add all three vars to `.env`:**

```bash
LANGSMITH_API_KEY=your-key-here   # from smith.langchain.com → Settings → API Keys
LANGSMITH_PROJECT=cogni-graph     # project name — created automatically on first trace
LANGSMITH_TRACING_V2=true        # master switch — required, not optional
```

**3. Restart the API** (env vars are loaded once at startup):

```bash
pkill -f "uvicorn api:app"
cd backend && uvicorn api:app --host 0.0.0.0 --port 8000
```

**4. Send an agent query** to generate the first trace:

```bash
curl -sN -X POST http://localhost:8000/query/agent \
  -H "Content-Type: application/json" \
  -d '{"question": "Who owns the Lease Renewal workflow?"}'
```

**5. Open LangSmith** → Projects → `cogni-graph`. Traces appear within seconds.

### Verified trace output

One agent query produces 5 runs in LangSmith (verified live):

| Run | Type | Latency | What it captured |
|-----|------|---------|-----------------|
| ChatAnthropic | `llm` | ~7 s | Turn 1 — tool_use decision, input messages, output tool blocks, token counts |
| execute_graph_tool | `tool` | ~0 s | Tool name + input + full result returned to Claude |
| ChatAnthropic | `llm` | ~7 s | Turn 2 — next decision |
| execute_graph_tool | `tool` | ~0 s | Second tool call input + result |
| ChatAnthropic | `llm` | ~2 s | Final turn — end_turn, full answer text, output tokens |

### Troubleshooting — nothing appearing in LangSmith

| Symptom | Cause | Fix |
|---------|-------|-----|
| No runs at all | `LANGSMITH_TRACING_V2` missing or not `true` | Add `LANGSMITH_TRACING_V2=true` to `.env` |
| Runs missing after adding key | API not restarted after `.env` change | `pkill -f uvicorn && cd backend && uvicorn api:app` |
| Wrong project shown | `LANGSMITH_PROJECT` not set | Add `LANGSMITH_PROJECT=cogni-graph` to `.env` |
| Standard `/query` has fewer runs | SSE streaming call not fully auto-traced | Use `/query/agent` for the richest trace trees |

### Using traces for evaluation

LangSmith traces can be added to evaluation datasets directly from the UI:

1. Find a trace in the LangSmith project
2. Click **Add to Dataset** → select or create a dataset
3. Run evaluations with custom or built-in evaluators (e.g. correctness, relevance)
4. Compare runs across model versions or prompt changes

This is the production path from ad-hoc tracing to structured offline evaluation — complementing the `eval.py` entity-recall harness with LLM-judged quality metrics.

---

## Running the Project

### Prerequisites

```bash
# 1. Start Neo4j
docker compose up -d          # wait ~15 s

# 2. Activate the Python environment
source .venv/bin/activate

# 3. Seed the Meridian Property Group graph
python backend/seed.py

# 4. Start the API
cd backend && uvicorn api:app --reload       # http://localhost:8000

# 5. Start the UI
cd UI && npm run dev           # http://localhost:5176
```

### Key URLs

| URL | What it is |
|-----|-----------|
| `http://localhost:5176` | React UI — Graph, Query, Source tabs |
| `http://localhost:8000/docs` | FastAPI auto-generated API docs |
| `http://localhost:8000/metrics` | Live observability: tokens, cost, model routing, cache hit rate |
| `http://localhost:7474` | Neo4j browser (neo4j / companygraph123) |
| `https://smith.langchain.com` | LangSmith — trace explorer, evaluation datasets, run comparisons |

### Query endpoints

```bash
# Standard query — full graph in cached system prompt, model-routed
curl -N -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "who owns the lease renewal workflow"}'

# Agentic query — iterative tool-calling loop, streams tool events
curl -N -X POST http://localhost:8000/query/agent \
  -H "Content-Type: application/json" \
  -d '{"question": "trace the compliance impact of the GDPR decision"}'

# Hybrid BM25 search
curl "http://localhost:8000/search?q=fair+housing+compliance"

# Observability snapshot
curl http://localhost:8000/metrics
```

### Running tests

```bash
# Unit tests only — no external services needed (~0.5 s)
python3 -m pytest tests/test_unit_bm25.py tests/test_unit_routing.py -v

# All tests except LLM calls — fast, 176 tests
python3 -m pytest tests/ -m "not llm"

# Full suite including LLM tests (calls Claude, costs money)
python3 -m pytest tests/

# See tests/README.md for the full test reference
```
