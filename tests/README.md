# Tests

Test suite for the Meridian Property Group knowledge graph project.

## Structure

```
tests/
  conftest.py                  shared fixtures, markers, SSE helper
  test_unit_bm25.py            BM25 algorithm, tokenizer, node-to-text (no services needed)
  test_unit_routing.py         route_query, _try_direct_answer, cost budget enforcement (no services needed)
  test_unit_safety.py          input injection defence (5 families) + output PII scanning (SSN, card, routing, email)
  test_integration_graph.py    graph.py functions against live Neo4j + seed data integrity
  test_integration_api.py      all REST endpoints, SSE streams, CRUD operations
```

## Prerequisites

```bash
# From the project root — activate the venv
source .venv/bin/activate

# Install pytest (already in requirements.txt)
pip install -r requirements.txt
```

Integration and API tests also require:
- **Neo4j** running: `docker compose up -d` (wait ~15 s)
- **API** running: `cd backend && uvicorn api:app` or `cd backend && python api.py`
- **Seed data** loaded: `python backend/seed.py`

## Running tests

### Unit tests only — no external services needed

```bash
python3 -m pytest tests/test_unit_bm25.py tests/test_unit_routing.py tests/test_unit_safety.py -v
```

### All tests except LLM calls — fast, ~1 s

```bash
python3 -m pytest tests/ -m "not llm"
```

### Full suite including LLM tests — calls Claude, costs money

```bash
python3 -m pytest tests/
```

### Integration tests only (Neo4j + API must be running)

```bash
python3 -m pytest tests/ -m "integration and not llm"
```

### LLM tests only

```bash
python3 -m pytest tests/ -m "llm"
```

### One specific file or class

```bash
python3 -m pytest tests/test_integration_graph.py -v
python3 -m pytest tests/test_integration_graph.py::TestSeedDataIntegrity -v
python3 -m pytest tests/test_integration_api.py::TestSearch -v
```

## Markers

| Marker | Meaning | Skip with |
|--------|---------|-----------|
| `integration` | requires Neo4j + API running | `-m "not integration"` |
| `llm` | calls the Claude API (slow, costs money) | `-m "not llm"` |

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_BASE_URL` | `http://localhost:8000` | Override API URL for integration tests |

```bash
API_BASE_URL=http://staging:8000 python3 -m pytest tests/ -m "not llm"
```

## CI/CD Integration

These tests run automatically in GitHub Actions on every push and pull request via `.github/workflows/ci.yml`.

### How the CI pipeline uses these tests

```
Job: syntax-and-unit
  └── python3 -m pytest tests/test_unit_bm25.py tests/test_unit_routing.py tests/test_unit_safety.py
      No external services. Runs in ~0.5 s.

Job: prompt-validation
  └── python3 scripts/validate_prompts.py
      Validates all backend/prompts/*.yaml before any integration tests run.

Job: integration  (needs syntax-and-unit + prompt-validation to pass)
  ├── Neo4j service container (auto-provisioned by GitHub Actions)
  ├── python backend/seed.py
  ├── python3 -m pytest tests/test_integration_graph.py -m "integration and not llm"
  ├── cd backend && uvicorn api:app &  (API started as background process)
  └── python3 -m pytest tests/test_integration_api.py -m "integration and not llm"
```

### What runs in CI vs. locally

| Test group | CI (push/PR) | Local (full suite) |
|------------|-------------|-------------------|
| Unit tests | ✅ Always | ✅ Always |
| Prompt validation | ✅ Always | ✅ `python3 scripts/validate_prompts.py` |
| Integration (graph + API, no LLM) | ✅ Always | ✅ With `-m "not llm"` |
| LLM tests (call Claude) | ❌ Skipped | Optional — `pytest -m "llm"` |

### Nightly eval (separate workflow)

The `eval-nightly.yml` workflow runs `eval.py` daily against the full API including LLM calls, then checks quality thresholds via `scripts/check_eval_regression.py`. This is separate from the `pytest` suite.

### Dummy API key in CI

The integration job sets `ANTHROPIC_API_KEY: sk-ant-dummy-key-for-ci-integration-tests`. This is intentional — the integration tests are all marked `-m "not llm"` so no actual Anthropic API calls are made. The key is only needed to satisfy the SDK import at startup.

## What each file tests

### `test_unit_bm25.py` — 21 tests

Verifies the BM25 algorithm in isolation:

- `_tokenize` — lowercasing, punctuation stripping, edge cases
- `_bm25_score` — IDF weighting, term frequency, document-length normalisation, empty inputs
- `_node_to_text` — field extraction, missing fields, field concatenation

### `test_unit_routing.py` — 37 tests

Verifies query routing, direct-answer logic, and cost budget enforcement with Neo4j mocked:

- `route_query` — simple lookups → haiku, complexity indicators → sonnet, long questions → sonnet
- `_try_direct_answer` — count queries, list queries, correct Neo4j label mapping, non-direct questions return `None`
- `TestCostBudgetEnforcement` — 10 tests: normal routing below budget, Haiku forced for all queries when exceeded, `_update_metrics` flag-setting at threshold, disabled-when-zero behaviour, token state isolation between tests

### `test_unit_safety.py` — 53 tests

Verifies the prompt injection defence layer (`_check_injection`) in isolation — no external services needed:

| Class | Tests | What it covers |
|-------|-------|---------------|
| `TestInstructionOverride` | 8 | "ignore/disregard/forget/override instructions" variants, case insensitivity |
| `TestPromptExtraction` | 8 | "reveal/show/print/repeat your system prompt", "what are your instructions" |
| `TestIdentityOverride` | 6 | "you are now", "pretend to be", "roleplay as", "simulate being" |
| `TestJailbreakKeywords` | 6 | "jailbreak", "DAN mode", "developer mode", "godmode" |
| `TestDelimiterInjection` | 5 | `<system>`, `[SYSTEM]`, `### system`, `ASSISTANT:`, `SYSTEM:` |
| `TestLengthGuard` | 4 | At-limit passes, 1-over blocked, far-over blocked, error message format |
| `TestLegitimateQuestions` | **16** | **All 6 sample PropTech questions + 10 domain phrases verified as false-positive free** |

The `TestLegitimateQuestions` class is the false-positive guard — any new pattern added to `_INJECTION_PATTERNS` must keep all 16 tests green.

### `TestOutputSafety` — 14 tests

Verifies `_scan_output()` — PII detection and redaction in LLM responses:

| Tests | What they cover |
|-------|----------------|
| 2 | SSN (`NNN-NN-NNNN`) — detected, surrounding text preserved |
| 4 | Payment cards — formatted spaces/dashes, unformatted Visa/MC/Amex |
| 1 | Bank routing number (9-digit ABA format) |
| 2 | External email — detected; internal `@meridianpg.com` NOT flagged |
| 5 | Clean text — MRR/ARR amounts, unit counts, dates, versions never trigger false positives; multiple PII types redacted together; return type check |

### `test_integration_graph.py` — 65 tests

Verifies `graph.py` functions against the live Meridian Property Group dataset:

- `graph_stats` — correct node and relationship counts
- `list_nodes` — filtering by label, limit, field presence
- `get_node` / `get_node_with_connections` — known entities, connection fields, direction values
- `get_full_graph` — full node and relationship counts
- `search_nodes` — name match, case insensitivity, label filter
- `hybrid_search_nodes` — BM25 ranking quality, label filter, fallback
- `find_shortest_path` — direct and multi-hop paths, no-path case
- `create_node` / `delete_node` / `create_relationship` — full CRUD lifecycle
- `TestSeedDataIntegrity` — 10 assertions verifying the PropTech dataset is correctly wired (ownerships, dependencies, AFFECTS relationships, product statuses)

### `test_integration_api.py` — 63 tests

Verifies every REST endpoint via HTTP:

| Class | Endpoint | Tests |
|-------|----------|-------|
| `TestHealth` | `GET /` | status, stats, node counts |
| `TestMetrics` | `GET /metrics` | all keys, model routes, cost ≥ 0 |
| `TestFullGraph` | `GET /graph` | node/rel counts, structure |
| `TestBrief` | `GET /brief` | 200, PropTech content |
| `TestListNodes` | `GET /nodes` | all 30, label filter, limit |
| `TestGetNodeById` | `GET /nodes/{id}` | known node, connections, 404 |
| `TestCreateNode` | `POST /nodes` | 201, retrievable, missing name → 422, all labels |
| `TestDeleteNode` | `DELETE /nodes/{id}` | 200, id in response, gone after, 404 |
| `TestCreateRelationship` | `POST /relationships` | 201, visible in connections, invalid ids → 404 |
| `TestSearch` | `GET /search` | hybrid ranking, keyword mode, type filter, no results |
| `TestPath` | `GET /path` | direct, multi-hop, no path → 404 |
| `TestImpact` | `GET /impact/{id}` | source + reachable, hops field, 404 |
| `TestQueryDirect` | `POST /query` | direct route (no LLM), latency < 1 s, SSE events |
| `TestQueryLLM` *(llm)* | `POST /query` | answer text, haiku/sonnet routing, metrics update |
| `TestQueryAgent` *(llm)* | `POST /query/agent` | tool calls emitted, final text, done metadata |
