# Demo Video Script — SCIPAB Edition
## CogniGraph — Design Decisions, Told as a Story

**Purpose:** A decision-first walkthrough of CogniGraph framed in **SCIPAB** —
Situation, Complication, Implication, Position, Action, Benefit — so the
*why* behind every architectural choice leads, and the code follows.

**Target role:** Lead AI Engineer
**Total runtime:** ~7–8 minutes
**Format:** Screen recording with voiceover

| SCIPAB | What it answers | Scene |
|--------|-----------------|-------|
| **S**ituation | The shared starting context | 1 |
| **C**omplication | What's hard / what changed | 2 |
| **I**mplication | Why that matters if ignored | 3 |
| **P**osition | My thesis / point of view | 4 |
| **A**ction | The design decisions I made | 5 (the core) |
| **B**enefit | The payoff | 6 |

> Companion to `DESIGN_DECISIONS.md` (the full decision log) and `VIDEO_SCRIPT.md`
> (the feature-by-feature demo). This script is the *narrative* version.

---

## SCENE 1 — SITUATION
**Duration: ~45 seconds**

**ON SCREEN:** Title card → the company brief (`backend/nexus_corp_brief.md`).

> "Every company's most valuable knowledge lives in documents — briefs, wikis, decision logs, org charts. And in a regulated domain like PropTech, the questions that matter are *structural*: who approved a lease policy, which products fall under a new GDPR rule, what breaks if one engineer leaves.
>
> Our scenario is **Meridian Property Group**, a fictional PropTech SaaS company. Its entire reality — people, products, customers, workflows, decisions — starts life as one plain-text brief."

**SCIPAB:** *Situation — the shared, uncontroversial starting point.*

---

## SCENE 2 — COMPLICATION
**Duration: ~45 seconds**

**ON SCREEN:** Split view — a keyword search returning nothing useful next to a flat chatbot guessing.

> "Here's the tension. Those structural questions are about *relationships* — and you can't recover relationships by keyword-searching a pile of files, or by retrieving document chunks with vanilla RAG. Chunks don't know who *owns* a workflow or what a decision *affects*.
>
> And even if you bolt an LLM on top, a naive build is expensive, opaque, unsafe with PII, and impossible to evaluate or trust. Every one of those is disqualifying in property tech."

**SCIPAB:** *Complication — why the obvious approaches fail.*

---

## SCENE 3 — IMPLICATION
**Duration: ~40 seconds**

**ON SCREEN:** Three consequences fade in — "Wrong compliance answers" · "Runaway cost" · "No way to trust or improve it."

> "If you ignore that, the consequences are concrete. You get confidently wrong answers on compliance and risk questions — the exact ones with legal and financial weight. You get unpredictable cost as every query hits your most expensive model. And you get a black box you can't observe, can't safely expose, and can't systematically improve.
>
> In a regulated domain, that's not a rough edge. It's a non-starter."

**SCIPAB:** *Implication — the stakes if the complication goes unaddressed.*

---

## SCENE 4 — POSITION
**Duration: ~40 seconds**

**ON SCREEN:** The component architecture diagram (README Mermaid) + the routing diagram.

> "So here's my position. The answer isn't a bigger model or a clever prompt — it's *architecture*, where every layer is a deliberate, documented decision.
>
> A knowledge graph for the data, because relationships should be first-class. Hybrid retrieval, because real search needs both keywords and meaning. Agentic tool-calling I own outright, because I want to see every turn. Tiered model routing and caching, because cost is a design problem. And safety, observability, and evaluation built in from the start — not bolted on.
>
> Let me walk you through those decisions — and the alternatives I rejected for each."

**SCIPAB:** *Position — the thesis that resolves the implication.*

---

## SCENE 5 — ACTION (the design decisions)
**Duration: ~4 minutes**

> Narration model for this scene: for each decision — **the choice → the alternative I rejected → the one-line why.** On screen, scroll the matching rows of `DESIGN_DECISIONS.md`.

### 5a — Data & graph
**ON SCREEN:** Neo4j graph view; `graph.py`.

> "**Neo4j over a relational or vector database.** Relationships between people, products, and decisions are first-class edges, not joins or embeddings — so a three-hop blast-radius query is one expressive Cypher traversal instead of N round-trips.
>
> **Typed labels and directed relationship types** — five node labels, eight relationship types — so path-finding and single-point-of-failure analysis are even *possible*.
>
> And **one `graph.py` data layer**, shared by the REST API, the MCP server, the seed loader, the eval harness, and the tests. One source of truth — add a capability once, every surface gets it."

### 5b — Ingestion
**ON SCREEN:** `doc_to_graph.py` + the company brief.

> "**Ingestion via Claude tool-use extraction, not regex parsing.** `doc_to_graph.py` forces a single structured tool call, so the model returns validated entities and relationships that drop straight into the graph schema. The same pipeline works for any prose document — RFCs, sales notes, org charts."

### 5c — Retrieval
**ON SCREEN:** the hybrid search badges (lexical / semantic).

> "**The full graph serialized into a prompt-cached system block, instead of per-query RAG.** At thirty nodes it fits in about two thousand tokens — so I cache it once rather than risk retrieval errors from chunk selection. I was explicit that this is a *scale-bounded* decision, with subgraph retrieval as the upgrade path.
>
> **Hybrid search: BM25 plus local semantic embeddings, fused with Reciprocal Rank Fusion.** Keywords for precision, embeddings for meaning — and the embeddings run *locally* with sentence-transformers, so there's no API key and no vector database to operate."

### 5d — Agents & orchestration
**ON SCREEN:** the single-agent and multi-agent harness diagrams.

> "**Native Anthropic tool-calling, not LangChain or LangGraph.** A forty-line loop I own completely — so I can stream custom typed events, attach traces precisely, and debug every turn with no framework abstraction in the way.
>
> **A multi-agent orchestrator on top of that** — planner, parallel workers, synthesizer — and, again, *no framework*: plain Python with `asyncio` for the fan-out. Purely additive; the single-agent path is untouched.
>
> **And an MCP server** — the same graph exposed as eleven tools over the Model Context Protocol, so Claude Desktop or any MCP client can use it with zero custom integration."

### 5e — Model selection & cost
**ON SCREEN:** the Observe tab — routing distribution + cost + cache.

> "**Three-tier routing.** List and count queries are answered straight from Neo4j with *no LLM call*. Simple lookups go to Haiku, multi-hop reasoning to Sonnet — and the routing decision is shown on screen, in plain language, for a non-technical stakeholder.
>
> **In the multi-agent path, per-role routing is the cost lever** — capable Sonnet for planning and synthesis, cheap Haiku for the parallel workers.
>
> **Prompt caching** marks the graph context ephemeral. And I'm precise about it: at this scale it's a *cost* lever, not a latency one. Plus a **daily budget cap** that auto-forces Haiku when spend crosses a threshold."

### 5f — Safety
**ON SCREEN:** an injection attempt returning HTTP 400; a redacted PII response.

> "**Defence in depth.** A prompt-injection filter blocks five attack families before any LLM call. A PII scanner redacts SSNs, card and routing numbers, and external emails *out* of model output — domain-aware, because internal directory emails are fine and leaked external PII is not. And structurally, the user's question stays in the user turn, separate from the cached system instructions."

### 5g — Observability, prompts & quality
**ON SCREEN:** LangSmith feed in the Observe tab; `prompts/*.yaml`; the test run.

> "**LangSmith tracing**, surfaced *inside* the app so a stakeholder without a login can still see every tool call and token. **Prompts versioned in YAML** — configuration, not code, swappable by an environment variable.
>
> And quality is not an afterthought: an **offline eval harness** scoring entity recall with a nightly regression gate, and a **four-tier test suite — 295 tests** — unit, integration, API, and opt-in LLM tests, all in CI."

**SCIPAB:** *Action — the concrete decisions, each with its rejected alternative.*

---

## SCENE 6 — BENEFIT
**Duration: ~40 seconds**

**ON SCREEN:** `DESIGN_DECISIONS.md` Section 6 (AI SDLC maturity table, ✅/⚠️/❌).

> "Put together, the payoff is a platform that is *production-shaped*, not a prototype. It answers the structural questions correctly because the data is a graph. It's cost-managed because routing and caching are design decisions. It's safe for a PII-sensitive domain, observable end to end, and measurably improvable through evaluation.
>
> But the deeper benefit is the one that matters in this role: every decision was made explicitly, the alternatives were weighed, and the trade-offs are documented — including the gaps and what I'd do next. That's the difference between writing code and *owning architecture*."

**SCIPAB:** *Benefit — the value, tied back to the Position.*

---

## One-paragraph SCIPAB (for the intro or a written summary)

> **Situation:** PropTech's most important knowledge is locked in documents, and the questions that matter are structural. **Complication:** keyword search and chunk-based RAG can't recover relationships, and a naive LLM build is expensive, opaque, and unsafe. **Implication:** in a regulated domain that means wrong compliance answers, runaway cost, and a system you can't trust or improve. **Position:** the answer is architecture — a knowledge graph with agentic AI, where every layer is a deliberate, documented decision. **Action:** graph over vectors; Claude tool-use ingestion; hybrid BM25-plus-semantic retrieval; native tool-calling and a no-framework multi-agent orchestrator; an MCP server; three-tier routing with caching and a budget cap; injection and PII guards; LangSmith observability; YAML-versioned prompts; and an eval harness with 295 tests in CI. **Benefit:** a production-shaped, cost-managed, observable, safe, and measurable platform — and a demonstration of owning architecture, not just writing code.
