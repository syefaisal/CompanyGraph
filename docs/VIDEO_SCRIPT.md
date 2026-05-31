# Demo Video Script
## CogniGraph — Agentic AI Knowledge Graph for PropTech
### Target role: Lead AI Engineer, RealPage

**Total runtime:** ~10 minutes  
**Format:** Screen recording with voiceover  
**Prep checklist before recording:**
- [ ] `docker compose up -d` (Neo4j healthy)
- [ ] `python backend/seed.py` (fresh PropTech data)
- [ ] `uvicorn api:app` running on :8000
- [ ] `npm run dev` running on :5173
- [ ] Browser open at `http://localhost:5173`
- [ ] LangSmith open at `smith.langchain.com → Projects → cogni-graph`
- [ ] Terminal with venv active, cwd = project root
- [ ] Font size bumped up for readability

---

## SCENE 1 — Opening & Problem Statement
**Duration: ~45 seconds**

**ON SCREEN:** README.md open in editor showing the top section

> "Property technology is a domain where decisions have real legal, financial, and operational consequences. Who approved a lease policy change? Which products are affected by a new GDPR requirement? Which engineer owns the workflow that would break if someone left the company?
>
> These are not semantic search questions. They are structural questions — and they need a system built around relationships, not document chunks.
>
> What I'm going to show you is CogniGraph: an agentic AI platform I built to demonstrate exactly the kind of architecture I'd bring to the RealPage team. It's a knowledge graph connecting people, products, customers, workflows, and decisions at a fictional PropTech company — with a multi-agent query layer, hybrid search, model routing, real-time streaming, LangSmith tracing, and an offline evaluation harness.
>
> Let me walk you through it layer by layer."

**JD ALIGNMENT:** Establishes PropTech domain relevance and sets up the architectural story.

---

## SCENE 2 — The Data: PropTech Knowledge Graph
**Duration: ~60 seconds**

**ON SCREEN:** Browser at `http://localhost:5173` — Graph tab

> "This is the Meridian Property Group knowledge graph. Thirty nodes, seventy-one relationships. Five entity types, all modelled after real PropTech concerns.
>
> Blue nodes are people — engineers, a compliance director, a leasing director. Purple nodes are products — LeaseTrack, MaintenanceOS, TenantPay. Green nodes are customers — property management firms, an HOA, a commercial REIT. Orange nodes are workflows — Lease Renewal, Work Order Processing, Fair Housing Audit. Red nodes are decisions — the GDPR and CCPA overhaul, a product deprecation, a market expansion.
>
> I want to draw your attention to a few relationships in particular."

**ON SCREEN:** Click the `Fair Housing Audit` node to highlight it and its connections

> "The Fair Housing Audit workflow is owned by the Director of Compliance. The Lease Renewal workflow depends on it — meaning any lease renewal must pass a fair housing check first. And the GDPR decision directly affects both LeaseTrack and TenantPay, the two products that handle the most tenant PII.
>
> These aren't hand-crafted. They were extracted from a plain-text company brief by Claude using structured tool-calling — which I'll show later. The point is: the domain model reflects real PropTech risk and compliance structure."

**JD ALIGNMENT:** *"Knowledge graphs; designing AI products in domains with strong regulatory or privacy constraints; PropTech domain needs."*

---

## SCENE 3 — Document Ingestion Pipeline
**Duration: ~45 seconds**

**ON SCREEN:** Click `Source` tab — show the nexus_corp_brief.md document

> "The source of this graph is a plain-text company brief — exactly the kind of document that exists in every company's wiki or Notion. No schema required from the author.
>
> A single script, `doc_to_graph.py`, sends this document to Claude Opus with a structured tool definition. Using `tool_choice: {type: 'tool'}`, Claude is forced to make exactly one structured call that returns every entity and relationship. No free-form parsing — the output is directly validated against the Neo4j schema.
>
> This is the realistic ingestion path: unstructured document → LLM extraction → graph database. The same pipeline works for org charts, engineering RFCs, sales notes, or any prose-heavy internal document. It's a reusable RAG ingestion framework."

**JD ALIGNMENT:** *"Reusable RAG pipelines and ingestion frameworks; prompting, tool use, function calling."*

---

## SCENE 4 — Model Routing & Cost Management
**Duration: ~60 seconds**

**ON SCREEN:** Switch to `Query` tab. Type: `list all workflows`

> "Before I show the AI reasoning, let me show the cost management layer — because this is where production AI systems win or lose on economics.
>
> I'm going to type the simplest possible question: 'list all workflows'."

**ON SCREEN:** Hit Enter — response appears instantly with no streaming cursor

> "Watch the response time. Under 30 milliseconds. No LLM was called at all.
>
> The system has a three-tier routing layer. List and count queries are intercepted before they reach Claude and answered directly from Neo4j. Simple entity lookups go to Claude Haiku — fast and cheap. Complex multi-hop reasoning goes to Claude Sonnet.
>
> I can prove this by checking the metrics endpoint."

**ON SCREEN:** Open new tab to `http://localhost:8000/metrics`

> "The metrics endpoint tracks every query in real-time. You can see the model routing distribution, the cache hit rate, average latency, and an estimated cost in USD. This is the kind of observability I'd build into any production AI service — not as an afterthought, but as a first-class design decision."

**JD ALIGNMENT:** *"Model routing, distillation, and caching strategies; right-sizing infrastructure; SLAs/SLOs for key AI services; observability, logging."*

---

## SCENE 5 — Hybrid Search
**Duration: ~30 seconds**

**ON SCREEN:** Open terminal, run:
```bash
curl "http://localhost:8000/search?q=compliance+audit"
```

> "The search layer uses BM25 — proper lexical ranking, not substring matching. BM25 weights terms by inverse document frequency, so rare terms like 'compliance' or 'GDPR' score higher than common words. This is the lexical half of hybrid search.
>
> The result: David Chen comes back first — he's the Director of Compliance. Then the GDPR decision, then the Fair Housing Audit. Exactly the right ranking, with no vector database needed at this scale.
>
> The design is explicit: BM25 now, dense vector embeddings when the graph grows. The retrieval architecture is built to evolve."

**JD ALIGNMENT:** *"Data and retrieval architecture — RAG, hybrid search, knowledge graphs; retrieval optimization techniques."*

---

## SCENE 6 — Standard Query with Streaming & Prompt Caching
**Duration: ~75 seconds**

**ON SCREEN:** Query tab. Type: `Which products does Sunstone Residential use and who built them?`

> "Now let me show the standard query mode. This is a customer-360 question — eleven words, no complex reasoning indicators — so it routes to Claude Haiku."

**ON SCREEN:** Hit Enter — watch tokens stream in

> "Watch the tokens arrive in real time. This is server-sent events — the API opens a streaming response and forwards tokens to the browser as they arrive. The UI renders them word by word.
>
> Under the hood, the full knowledge graph — all 30 nodes and 71 edges — is serialized into the system prompt and marked as a cached block with Anthropic's prompt caching API. The first query in a session pays full token cost. Every subsequent query within five minutes hits the cache at about ten times lower input cost.
>
> So this response — which correctly names LeaseTrack, MaintenanceOS, TenantPay, and their engineers Marcus Webb and Priya Okafor — costs a fraction of a cent to produce, because the context was already cached."

**JD ALIGNMENT:** *"Real-time streaming infrastructures; semantic caching; model selection strategy — small vs. large models; cost management."*

---

## SCENE 7 — Agentic Mode: Tool-Calling Loop
**Duration: ~120 seconds**

**ON SCREEN:** Query tab. Type: `Trace the full compliance impact of the GDPR and CCPA overhaul decision.`

> "This is the question that demonstrates the agentic architecture. It's complex — it touches decisions, products, workflows, customers, and people across multiple hops. It routes to Claude Sonnet, and I'm going to use the agent endpoint so you can see the reasoning trace.
>
> Let me switch to the terminal and call the agent endpoint directly so we can see every event as it arrives."

**ON SCREEN:** Run in terminal:
```bash
curl -sN -X POST http://localhost:8000/query/agent \
  -H "Content-Type: application/json" \
  -d '{"question": "Trace the full compliance impact of the GDPR and CCPA overhaul decision."}' \
| grep "data:" | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line.strip()[6:])
        t = e.get('type')
        if t == 'thinking': print(f'[thinking] {e[\"content\"][:80]}')
        elif t == 'tool_call': print(f'[tool]     → {e[\"tool\"]}({list(e[\"input\"].values())[0] if e[\"input\"] else \"\"})')
        elif t == 'tool_result': print(f'[result]   ← {e[\"result\"][:60]}...')
        elif t == 'done': print(f'[done]     tool_calls={e.get(\"tool_calls\")}  model={e.get(\"model\")}  latency={e.get(\"latency_ms\")}ms')
    except: pass
"
```

> "Watch what happens. Claude first thinks — reasons about what it needs to know. Then it calls `search_graph` to find the decision by keyword. Gets the ID back. Calls `trace_decision_impact` with that ID — which runs a three-hop graph traversal in Cypher. Then calls `get_entity` multiple times to pull full details on each affected product and workflow. Only then does it synthesize a final answer.
>
> This is the responder-thinker pattern from modern agentic design — the LLM is not just answering, it's planning a multi-step retrieval strategy and executing it. Each tool call is a deliberate decision.
>
> The SSE stream emits five typed events: `thinking`, `tool_call`, `tool_result`, `text`, and `done`. The UI can render each step as it happens — which is a critical UX pattern for agentic systems where users need to understand what the AI is doing."

**JD ALIGNMENT:** *"Multi-agent and workflow orchestration — responder/thinker pattern, tool calling, agentic frameworks; real-time streaming infrastructures; LLM-based application design — prompting, tool use, function calling, multi-agent workflows."*

---

## SCENE 8 — LangSmith Tracing
**Duration: ~75 seconds**

**ON SCREEN:** Switch to browser — LangSmith at `smith.langchain.com → Projects → cogni-graph`

> "Every agent query is traced in LangSmith. Let me show you what that looks like."

**ON SCREEN:** Click on the most recent trace run to expand it

> "Here's the full run tree for the query we just executed. At the top: the `agent_query` chain — the parent run. Inside it, you can see each LLM call as a `ChatAnthropic` node, and each tool execution as an `execute_graph_tool` node.
>
> Click into any LLM call and you see the exact input messages, the output, and the token counts. Click into any tool call and you see exactly what was passed in and what came back. Latency per step. Everything is captured.
>
> This is production-grade AI observability. You can build evaluation datasets directly from these traces — annotate the good runs, flag the bad ones, build a dataset, run LangSmith evaluators against it. That's the pipeline from ad-hoc tracing to rigorous offline evaluation.
>
> The integration is three lines in the codebase: `wrap_anthropic`, two `@traceable` decorators. The key thing — and this is a common gotcha — is that `LANGSMITH_TRACING_V2=true` must be set as the master switch. Just setting the API key is not enough."

**JD ALIGNMENT:** *"AI experiment tracking and evaluation frameworks — LangSmith Evals; observability, logging, and incident response for AI systems; offline and online metrics for relevance."*

---

## SCENE 9 — Evaluation Harness
**Duration: ~60 seconds**

**ON SCREEN:** Terminal. Run:
```bash
python backend/eval.py
```

> "Beyond tracing, the system has a structured offline evaluation harness. Eight PropTech test cases — workflow ownership, compliance impact, customer product mapping, path finding, risk analysis, decision tracing, and hybrid search quality.
>
> Each case scores entity recall — what fraction of expected entities appeared in the answer. Pass threshold is 60%. Watch the results come in."

**ON SCREEN:** Watch the eval run, results printing per test case

> "8 out of 8 passing. Average recall 97%. You can also see the model routing column — simpler questions like customer products and hybrid search correctly routed to Haiku, complex reasoning to Sonnet.
>
> And results are saved in two places. First: a local JSON file in `eval_results/` with a timestamp — so you can track quality over time and diff runs. Second: pushed to a LangSmith dataset called `cogni-graph-eval`, where each test case becomes a labelled example that can feed into LangSmith's evaluator framework.
>
> This is the measurable success criteria loop the JD asks for: define what good looks like, measure it, iterate."

**JD ALIGNMENT:** *"Define robust evaluation frameworks — offline metrics for relevance; model and retrieval evaluation; shape product roadmaps and define measurable success criteria for AI initiatives."*

---

## SCENE 10 — Human Evaluation & Responsible AI
**Duration: ~45 seconds**

**ON SCREEN:** Switch back to browser Query tab. Ask: `Who is responsible for fair housing compliance and what decisions have they influenced?`

> "One more pattern worth highlighting — and it maps directly to responsible AI governance."

**ON SCREEN:** After answer streams in — point to the thumbs-up / thumbs-down controls

> "Every AI response in the UI has a thumbs-up approve button and a thumbs-down flag button. Flagging opens a comment form where a reviewer can note exactly what was wrong — incorrect relationship, missing entity, wrong reasoning.
>
> Flagged responses accumulate in a Review sidebar. This is the human evaluation workflow for sensitive tasks. In a PropTech context, where an AI answer about fair housing compliance or GDPR scope could have real legal implications, you need a mechanism for a human to catch and annotate bad outputs before they propagate.
>
> The flags feed back into the LangSmith dataset pipeline — bad answers become labelled negative examples that improve your evaluation coverage over time."

**JD ALIGNMENT:** *"Human evaluation workflows for complex or sensitive tasks; content safety, bias and fairness; compliance with internal policies and external regulations — GDPR-like requirements."*

---

## SCENE 11 — Test Suite & Code Quality
**Duration: ~45 seconds**

**ON SCREEN:** Terminal. Run:
```bash
python3 -m pytest tests/ -m "not llm" -v --tb=short 2>&1 | tail -20
```

> "A production AI system needs tests — not just the LLM output, but the infrastructure underneath it.
>
> The project has 176 tests across four files. Unit tests for the BM25 algorithm — verifying IDF weighting, term frequency normalisation, empty inputs. Unit tests for the model routing logic — mocking Neo4j so they run in half a second with no services. Integration tests for every graph operation against live Neo4j. And a full API test suite covering all endpoints, SSE event structure, CRUD operations, and seed data integrity.
>
> 176 passing. The test architecture itself is a design document — it shows what the system guarantees and where the boundaries are."

**JD ALIGNMENT:** *"Guide architectural decisions and code quality; conduct thorough design and code reviews; modular reusable coding practices."*

---

## SCENE 12 — Architecture Close & Closing Statement
**Duration: ~60 seconds**

**ON SCREEN:** Open `DESIGN_DECISIONS.md` in editor — scroll through the table slowly

> "Let me close with the architecture picture.
>
> Every decision in this system was made explicitly and documented. Neo4j over a vector database — because relationships are first-class in PropTech data. BM25 over substring search — because IDF weighting matters for domain-specific terms. Three-tier model routing — because not every query deserves a Sonnet call. Native Anthropic tool-calling over LangChain — because I want full visibility into every turn without framework abstraction hiding what's happening. LangSmith over custom logging — because traces should be searchable, annotatable, and feedable into eval datasets.
>
> The domain is property technology because that's where the interesting AI problems live right now: regulatory compliance, fair housing, tenant data privacy, lease management, vendor risk. These aren't generic enterprise AI problems — they're PropTech-specific, and this system is built to reflect that.
>
> The architecture I'd bring to RealPage is what you've just seen: agentic systems with real tool-calling loops, hybrid retrieval, model routing that manages cost, full observability from metrics to LangSmith traces to human feedback, and an evaluation harness that produces measurable numbers. That's the foundation for a production AI platform — not just a demo."

**JD ALIGNMENT:** Closes the full loop across all six JD responsibility areas.

---

## Recording Notes

**Sequence of browser tabs to have open before recording:**
1. `http://localhost:5173` — UI (Graph tab pre-loaded)
2. `http://localhost:8000/metrics` — Metrics
3. `smith.langchain.com` — LangSmith project `cogni-graph`
4. `DESIGN_DECISIONS.md` in editor

**Terminal commands to pre-type (don't run yet):**
```bash
# Scene 4
curl "http://localhost:8000/search?q=compliance+audit"

# Scene 7
curl -sN -X POST http://localhost:8000/query/agent \
  -H "Content-Type: application/json" \
  -d '{"question": "Trace the full compliance impact of the GDPR and CCPA overhaul decision."}' \
| grep "data:" | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line.strip()[6:])
        t = e.get('type')
        if t == 'thinking': print(f'[thinking] {e[\"content\"][:80]}')
        elif t == 'tool_call': print(f'[tool]     → {e[\"tool\"]}({list(e[\"input\"].values())[0] if e[\"input\"] else \"\"})')
        elif t == 'tool_result': print(f'[result]   ← {e[\"result\"][:60]}...')
        elif t == 'done': print(f'[done]     tool_calls={e.get(\"tool_calls\")}  model={e.get(\"model\")}  latency={e.get(\"latency_ms\")}ms')
    except: pass
"

# Scene 9
python backend/eval.py

# Scene 11
python3 -m pytest tests/ -m "not llm" -v --tb=short 2>&1 | tail -20
```

**Queries to type in the UI (in order):**
1. Scene 4: `list all workflows`
2. Scene 6: `Which products does Sunstone Residential use and who built them?`
3. Scene 10: `Who is responsible for fair housing compliance and what decisions have they influenced?`

---

## JD Coverage Map

| JD Requirement | Demo Scene |
|---|---|
| Model selection strategy (small vs. large) | Scene 4, 6 |
| Multi-agent / tool calling / responder-thinker | Scene 7 |
| RAG, hybrid search, knowledge graphs | Scenes 2, 5, 6 |
| Real-time streaming | Scenes 6, 7 |
| Reusable RAG pipelines and ingestion | Scene 3 |
| Observability, logging, incident response | Scenes 4, 8 |
| Evaluation frameworks (offline metrics) | Scene 9 |
| Human evaluation workflows | Scene 10 |
| GDPR / compliance / responsible AI | Scenes 2, 7, 10 |
| LangSmith / AI experiment tracking | Scene 8 |
| Code quality / test standards | Scene 11 |
| PropTech domain expertise | All scenes |
| Cost management / right-sizing | Scene 4, 6 |
| Semantic caching | Scene 6 |
