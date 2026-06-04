# Interview Preparation Guide
## RealPage — Lead AI Engineer

---

## 1. Technical Topics to Master

| Topic | What to Know | Study Resources | Depth Required |
|-------|-------------|-----------------|---------------|
| **RAG architectures** | Chunking strategies (fixed, semantic, hierarchical), embedding models, vector stores (Pinecone, Weaviate, pgvector), reranking (cross-encoders, Cohere Rerank), hybrid search (BM25 + dense), late interaction (ColBERT), eval metrics (RAGAS, MRR, NDCG) | LlamaIndex docs, RAGAS paper, Pinecone learning center | Deep — expect "design a RAG system for X" |
| **Knowledge graphs** | Graph vs. vector store tradeoffs, property graph model, Cypher query patterns, multi-hop traversal, graph RAG (Microsoft GraphRAG), when graphs beat embeddings (structural queries, relationship chains) | Neo4j docs, Microsoft GraphRAG paper | Deep — you have live project to reference |
| **Agentic design patterns** | ReAct, responder/thinker, Plan-and-Execute, reflection loops, tool calling, function calling spec (OpenAI + Anthropic), agent memory (episodic, semantic, procedural), multi-agent orchestration, handoff protocols | Anthropic agent docs, LangGraph docs, AutoGen paper | Deep — central to the role |
| **LLM internals** | Transformer architecture (enough to explain attention, context window, KV cache), RLHF, fine-tuning vs. prompting vs. RAG decision, quantization (GGUF, GPTQ), distillation, model routing by capability/cost | Andrej Karpathy's LLM talk, HuggingFace docs | Medium — not ML research, but production tradeoffs |
| **Prompt engineering** | System prompt design, few-shot vs. zero-shot, chain-of-thought, structured output (JSON mode, tool_choice: tool), prompt versioning, prompt injection defense, temperature and sampling | Anthropic prompt engineering guide | Deep — shows craft |
| **Streaming architectures** | SSE vs. WebSocket vs. polling tradeoffs, backpressure, token streaming, async generators, chunked transfer encoding | FastAPI docs, MDN SSE spec | Medium |
| **Model evaluation** | Offline metrics (entity recall, BLEU, ROUGE, G-Eval, LLM-as-judge), online metrics (click-through, thumbs up/down, session depth), A/B testing for AI, red-teaming, bias evaluation | LangSmith Evals, HELM benchmark | Medium-Deep |
| **LangSmith / observability** | Tracing (run trees, spans, metadata), datasets, evaluators, prompt versioning, comparison views, feedback annotation, production monitoring | LangSmith docs | Medium — you have live integration |
| **Cost optimization** | Prompt caching (Anthropic, OpenAI), model routing (capability tiers), token budgeting, batching, distillation, semantic caching (GPTCache), output caching | Anthropic pricing docs, GPTCache | Deep — JD specifically calls this out |
| **Vector databases** | Approximate nearest neighbor (HNSW, IVF), cosine vs. dot product vs. Euclidean, metadata filtering, hybrid search, managed vs. self-hosted, pgvector for OLTP | Pinecone docs, Weaviate docs | Medium |
| **Agent frameworks** | LangGraph (stateful graphs, cycles, conditional edges), LangChain (chains, agents), Anthropic Agents SDK, Google ADK, AutoGen, CrewAI — tradeoffs between them | LangGraph quickstart, Google ADK docs | Medium — know the landscape even if you chose native SDK |
| **Containerization & deployment** | Docker multi-stage builds, docker-compose for local dev, Kubernetes (deployments, services, HPA, resource limits), CI/CD for ML (model versioning, canary deploys) | Docker docs, Kubernetes docs | Medium |
| **Python async patterns** | asyncio, async generators, concurrent.futures, background tasks (FastAPI BackgroundTasks, asyncio.ensure_future), event loops | Python asyncio docs | Deep — you use it in the project |
| **TypeScript/React** | React hooks, streaming state management, SSE in browser (ReadableStream, EventSource), TypeScript generics, Vite proxy config | React docs, MDN Streams API | Medium |

---

## 2. System Design Questions to Prepare

| Question | Key Points to Cover | Trap to Avoid |
|----------|--------------------|--------------------|
| **"Design a RAG system for RealPage's lease document corpus"** | Ingestion pipeline (chunking strategy for legal docs), embedding model choice (domain-specific vs. general), vector store selection, hybrid retrieval (BM25 + dense), reranker, prompt construction, caching, evaluation loop, PII redaction before indexing | Don't jump straight to implementation — start with requirements (latency? accuracy? cost? freshness?) |
| **"How would you build a multi-agent system for property compliance monitoring?"** | Agent roles (monitor agent, research agent, report agent), orchestration pattern (LangGraph stateful graph vs. sequential), tool definitions, memory across turns, human-in-the-loop checkpoints, failure modes | Don't ignore failure modes and cost — compliance agents can loop expensively |
| **"How do you decide between fine-tuning and RAG?"** | Finetuning: stable knowledge, style/format, latency-sensitive. RAG: dynamic/updatable knowledge, source attribution needed, low-data regime. Hybrid: finetuned model + RAG retrieval. For PropTech: RAG wins for lease/reg docs because they change | Don't say "always RAG" or "always finetuning" — it depends on data freshness and task type |
| **"Design an AI observability platform for a team of 10 AI engineers"** | Tracing (LangSmith/Langfuse), metrics (latency P50/P95/P99, token usage, cost/query, cache hit rate), alerting (error rate SLO, latency SLO), eval pipeline, prompt versioning, incident runbook | Don't forget the human side — who gets paged, how are incidents investigated |
| **"How would you build a model routing system at scale?"** | Intent classification (rule-based, small classifier, or LLM), routing dimensions (complexity, latency, cost, safety), fallback strategy, A/B testing routes, monitoring routing accuracy over time | Don't make it over-engineered — sometimes 12 words < sonnet is enough |
| **"How do you prevent vendor lock-in with LLM providers?"** | Abstraction layer (LiteLLM, custom adapter), eval-driven provider comparison, contractual SLAs, data residency requirements, open-source alternatives (Llama 3, Mistral) as fallback | Don't dismiss the business reality — switching costs are real, abstraction has maintenance cost |

### Sample Answers — System Design

---

**Q: "Design a RAG system for RealPage's lease document corpus."**

> "Before I touch architecture, I'd ask three questions: What's the latency target — sub-second for a leasing agent chatbot or a few seconds for a back-office analyst tool? How frequently do leases change — are we indexing once or continuously? And what's the compliance requirement — can PII from tenant documents appear in answers, or must it be redacted at index time?
>
> Given typical PropTech constraints — hundreds of thousands of leases, moderate freshness requirements, PII sensitivity — I'd design it like this:
>
> **Ingestion:** Parse PDFs to text, chunk semantically at clause boundaries rather than fixed tokens because legal docs have natural structure. Redact PII — SSNs, payment info — before embedding. Tag each chunk with metadata: lease ID, property ID, state jurisdiction, effective date.
>
> **Retrieval:** Hybrid BM25 + dense vectors with metadata pre-filtering. BM25 handles exact legal terminology ('force majeure', 'holdover tenant'). Dense handles semantic similarity. Cohere Rerank or a cross-encoder reranks the top-20 candidates to top-5.
>
> **Generation:** Inject retrieved chunks into the system prompt with source citations. Use structured output so the answer cites the specific lease clause. Cache frequent queries — 'what is the standard late fee clause?' hits many leases with the same answer.
>
> **Evaluation loop:** RAGAS scores for faithfulness and answer relevance. Human annotation pipeline for edge cases. Nightly regression eval against a golden dataset. Alert if faithfulness drops below 0.85.
>
> The thing I'd be most careful about: tenant PII in retrieval results. Every retrieved chunk needs a PII scan before it enters the prompt context. That's a compliance requirement, not an afterthought."

---

**Q: "How would you build a multi-agent system for property compliance monitoring?"**

> "I'd start with the problem: compliance monitoring in PropTech means watching for fair housing violations, lease term deviations, maintenance SLA breaches, and regulatory deadlines — across thousands of units. That's a continuous monitoring problem, not a one-shot query.
>
> I'd design three cooperating agents:
>
> **Monitor Agent** — a scheduled agent that ingests new leases, maintenance records, and audit logs. It runs structured checks: 'Did this lease renewal screening decision match fair housing criteria?' It writes findings to a shared state store.
>
> **Research Agent** — triggered on anomalies from the Monitor. It can call external tools: look up the Fair Housing Act for the relevant state, check if a maintenance ticket exceeded the contractual SLA, cross-reference the lease against current rent control ordinances. It produces a structured finding report.
>
> **Report Agent** — assembles findings into a human-readable compliance dashboard and routes critical findings to a human reviewer queue.
>
> For orchestration, I'd use a LangGraph stateful graph rather than sequential chains — because compliance workflows have conditional edges ('if finding is critical, route to legal review; if minor, log and continue') and need the ability to pause and wait for human input. The human-in-the-loop checkpoint is non-negotiable for anything that could result in a fair housing violation finding.
>
> The failure modes I'd be most careful about: agents that loop because a tool call fails and they retry indefinitely, and cost explosion from the Research agent calling LLMs on every maintenance ticket. I'd rate-limit tool calls, set a hard iteration cap of 10, and use a small classifier to triage which anomalies actually need the Research agent."

---

**Q: "How do you decide between fine-tuning and RAG?"**

> "The decision tree I use has three branches:
>
> **Is the knowledge static or dynamic?** If the information changes frequently — lease terms, regulations, property prices — RAG wins every time. Fine-tuning bakes knowledge into weights that become stale. For PropTech, almost everything is dynamic: regulations change state by state, leases are renewed annually, policies shift. RAG is the right default.
>
> **Does the task require precise recall or stylistic adaptation?** If you need to answer 'what does clause 12.3 say?' you need retrieval — the model can't memorize millions of lease clauses. If you need the model to output structured JSON in a specific format, or adopt the tone of a compliance officer, fine-tuning can help — though few-shot prompting often gets you 80% of the way there at zero training cost.
>
> **What's the latency budget?** Fine-tuned models can be smaller and faster. If you need sub-200ms responses and the knowledge is truly stable, a fine-tuned small model beats RAG with retrieval latency. But that's rare in enterprise settings.
>
> For RealPage specifically, I'd default to RAG for anything touching lease content, regulations, or property data — because that data has both high freshness requirements and PII sensitivity that you'd need to scrub before fine-tuning anyway. I'd use fine-tuning only for output format adaptation — structured extraction schemas, tone, specific response templates — layered on top of retrieval."

---

**Q: "Design an AI observability platform for a team of 10 AI engineers."**

> "I've thought about this a lot because observability is where most AI teams accumulate invisible debt. The platform needs to serve three distinct consumers: engineers debugging a specific query, product managers tracking quality trends, and ops who need to know when to page someone.
>
> **Layer 1 — Tracing:** Every LLM call, every tool execution, every retrieval gets a span. LangSmith handles this well. The key is tagging spans with business-meaningful metadata — which product feature triggered this, which user tier, which model version — not just technical IDs. That's what lets you answer 'did the new prompt hurt quality for enterprise customers specifically?'
>
> **Layer 2 — Metrics:** Latency P50/P95/P99, cost per query by model tier, cache hit rate, error rate by endpoint. Prometheus + Grafana or a managed equivalent. The SLOs I'd set: P95 latency under 3s for user-facing endpoints, error rate under 0.5%, cost per query under $0.05.
>
> **Layer 3 — Eval pipeline:** Nightly automated eval against a golden dataset — entity recall, faithfulness, answer relevance. Regression alert if any metric drops more than 5%. Human annotation queue for flagged outputs with a weekly review cadence.
>
> **Layer 4 — Prompt versioning:** Prompts are config, not code. Every prompt change is versioned in YAML, deployed via env var, and tied to an eval run so you can A/B compare prompt versions against the same golden dataset before shipping to production.
>
> **Incident process:** Automated alert if error rate spikes → on-call engineer gets a LangSmith trace link with the failing query pre-loaded → runbook in the repo with common failure modes. Time-to-diagnose should be under 15 minutes for any LLM-related incident."

---

**Q: "How would you build a model routing system at scale?"**

> "The core insight is that routing is a cost-quality optimization problem, and the solution depends on your query distribution. Most systems have a power law: 20% of query types account for 80% of volume, and most of those are simple.
>
> I'd build a three-tier system — which I actually implemented in CogniGraph as a proof of concept. The tiers are: Direct (no LLM, deterministic answer from the data layer), Haiku or equivalent cheap model (fast, low-cost for structured lookups), and Sonnet or equivalent full model (complex reasoning when needed).
>
> The routing logic itself: start with a rule-based classifier because it's fast, cheap, interpretable, and easy to tune. Keyword indicators, question length, presence of reasoning-heavy tokens like 'trace', 'impact', 'why', 'compare'. This handles 80% of cases correctly and costs zero tokens. For the 20% of ambiguous cases, you can add a small classifier — a fine-tuned Haiku or a BERT model — to make the call.
>
> What I'd instrument: routing accuracy (compare the routing decision against a human-labelled set), cost saved by not routing to Sonnet, and latency distribution per tier. Set an alert if routing accuracy drops — it usually means your user query distribution has shifted and your rules need updating.
>
> The one thing I'd resist: using a large model to classify before the main call. It defeats the purpose. The classifier must be faster and cheaper than the cheapest tier it's routing to."

---

**Q: "How do you prevent vendor lock-in with LLM providers?"**

> "Vendor lock-in with LLMs is real but often overstated. The honest answer is: you can't eliminate it, but you can make switching cheap enough that you're not trapped.
>
> The practical approach I'd take:
>
> **Abstraction at the call boundary only.** I wouldn't build a full provider-agnostic SDK — the abstraction cost is high and the use of provider-specific features like Anthropic's prompt caching or OpenAI's structured output is often worth the coupling. Instead, I'd abstract just the LLM call itself — a single `call_llm(model, messages, tools)` function that can be pointed at different providers. That's usually a day's work and buys significant flexibility.
>
> **Eval-driven provider selection.** Every 6 months, run your golden dataset against two or three providers. This gives you empirical data — not marketing claims — on which provider performs better on your actual queries. It also builds the muscle to switch if pricing or quality shifts.
>
> **Data residency and contractual requirements first.** For a PropTech company processing tenant PII, data residency requirements may constrain which providers you can use regardless of technical preferences. Understand those constraints before choosing a primary provider.
>
> **Keep an open-source fallback.** Llama 3 70B or Mistral can handle many tasks that previously needed GPT-4. Regularly test your critical workflows against open-source models — not to switch, but to know you could. That knowledge is leverage in commercial negotiations."

---

## 3. Behavioral & Leadership Stories (STAR Format)

Prepare one concrete story for each. Use real examples from your career.

| Question Theme | What They're Assessing | STAR Anchor Points |
|----------------|----------------------|-------------------|
| **"Tell me about an AI system you architected from scratch and shipped to production"** | Scope, decision-making, delivery | Situation: the business problem. Task: what you owned. Action: architecture choices and why. Result: scale, latency, cost, business impact |
| **"Describe a time you had to make a hard tradeoff between speed and quality in an AI system"** | Judgment under constraints | A real case where you shipped something imperfect, instrumented it, and iterated. Show data-driven thinking |
| **"How have you mentored engineers on LLMs or AI systems?"** | Leadership, communication | Specific person, specific gap you identified, how you closed it — pairing, design reviews, resources you shared |
| **"Tell me about a time an AI system failed in production"** | Incident response, maturity | Be honest. Show: detection (how you knew), diagnosis, fix, prevention. What observability you added after |
| **"How do you communicate AI risk or uncertainty to non-technical stakeholders?"** | Executive communication | A real exec conversation where you had to explain why the AI can't do X, or why it failed, or why the roadmap should change |
| **"Describe how you've built standards or best practices for an AI team"** | Platform thinking, culture | Prompt versioning, eval standards, code review checklists, runbooks — something you established and others adopted |
| **"Tell me about identifying a high-value AI opportunity that wasn't on the roadmap"** | Strategic thinking, initiative | You spotted a pattern (user behavior, business metric), proposed an AI solution, quantified the opportunity, got it prioritized |
| **"How have you handled a situation where the AI solution wasn't technically feasible but stakeholders were committed to it?"** | Stakeholder management | Managing expectations, proposing alternatives, being honest about limitations while keeping trust |

### Sample Answers — Behavioral (STAR Format)

> **Note:** Adapt these answers with your own specific numbers, company names, and team details. The structure and reasoning patterns are the core — personalize the details.

---

**Q: "Tell me about an AI system you architected from scratch and shipped to production."**

> **Situation:** Our team had a growing internal knowledge problem. Engineers spent hours every week searching Confluence, Slack, and Jira to answer questions that had already been answered somewhere — 'which service owns this API?', 'what's the oncall escalation path for this alert?'. We were a 200-person engineering org and the cost was real but invisible.
>
> **Task:** I was asked to evaluate whether an AI system could address this. I owned the architecture decision, the build, and ultimately the rollout.
>
> **Action:** I spent the first two weeks on requirements, not code. I interviewed 15 engineers to understand query patterns — 80% were simple factual lookups, 15% needed multi-hop reasoning across docs, 5% were complex synthesis tasks. That distribution drove the architecture: a knowledge graph for structured organizational data combined with RAG for unstructured docs, with a three-tier model routing layer so simple lookups didn't burn Sonnet tokens.
>
> For the graph layer, I chose Neo4j because the relationships — 'owns', 'depends on', 'escalates to' — were first-class, not joinable columns. For the RAG layer, hybrid BM25 plus dense vectors because domain-specific jargon like service names and team aliases needed exact lexical matching that pure embeddings missed. I wired LangSmith for tracing from day one — which proved invaluable when we had a latency regression three weeks post-launch.
>
> We shipped a Slack integration first, then a web UI. Ran a 30-day eval with a labelled golden set measuring answer accuracy.
>
> **Result:** Answer accuracy hit 91% on the golden set. P95 latency was 800ms for the Haiku tier, 4.2s for Sonnet. Engineers reported spending about 40% less time on internal search in our 6-week survey. Cost was approximately $180/month in LLM API fees — well within the budget for eliminating the time cost of 15+ engineers searching for answers daily.

---

**Q: "Describe a time you had to make a hard tradeoff between speed and quality in an AI system."**

> **Situation:** We were building a lease document extraction feature — automatically pulling key terms from uploaded lease PDFs into structured fields. The product team needed it live in six weeks for a major customer demo. A full accuracy evaluation against our golden set of 200 leases was showing 87% field extraction accuracy. The industry standard we'd committed to stakeholders was 95%.
>
> **Task:** I had to decide: delay launch to hit 95%, or ship at 87% with guardrails.
>
> **Action:** I ran the numbers. The 13% error rate clustered heavily on two field types — percentage-based escalation clauses and multi-party lease structures. Both had low volume in our customer's actual document mix. I proposed a tiered approach: ship 87% overall accuracy now, with a confidence threshold — any extraction below 0.75 confidence shows an 'unverified' flag and routes to a human reviewer queue. We built the flag in two days.
>
> I also set up a LangSmith eval that ran nightly against the golden set, so we had a daily accuracy number and could track improvement as we iterated on the extraction prompt.
>
> I presented this to the product and legal team with a clear framing: 87% automated with human review on low-confidence extractions is better than 0% automated with manual entry on everything, and we had a measurable path to 95%.
>
> **Result:** We shipped on time. In the first month, the human review queue handled about 8% of extractions. Six weeks later, prompt iteration and a few targeted fine-tuning examples on the escalation clause pattern pushed overall accuracy to 93%. The customer renewed with us partly citing the extraction feature. The principle I took from this: ship with honest measurement and a clear improvement path, not with silence about limitations.

---

**Q: "How have you mentored engineers on LLMs or AI systems?"**

> **Situation:** We hired two strong software engineers onto the AI team — excellent Python, great systems thinking, but no LLM experience. They were joining a project building an agent-based document processing system with tight deadlines.
>
> **Task:** I needed to get them productive on LLM work without creating a bottleneck where everything had to go through me.
>
> **Action:** I designed a three-week onboarding track, not a lecture series. Week one: implement a tool-calling loop from scratch — no LangChain, just the raw Anthropic SDK — that calls two custom tools. The goal was to understand what the SDK actually does, not just what a framework hides. I paired with each engineer for an hour a day reviewing their implementation and asking 'what happens if this tool call fails?', 'how do you know when the agent is done?'.
>
> Week two: take a real failing agent from our codebase and debug it. I gave them a loop that would run indefinitely and asked them to find and fix it. This taught them the failure modes in a safe environment.
>
> Week three: design and review. Each engineer designed their own component — prompt structure, tool schema, eval approach — and we did a design review where the other engineer and I asked hard questions.
>
> I also set up a shared prompt versioning repo where every prompt had a version number, a changelog, and an eval result. That gave new engineers a trackable artifact to iterate against rather than guessing.
>
> **Result:** Both engineers were shipping independently reviewed LLM components within six weeks. One of them identified a prompt injection vulnerability I'd missed in an existing system — better eyes than mine on the problem. The three-week track became the team's standard onboarding for new AI hires.

---

**Q: "Tell me about a time an AI system failed in production."**

> **Situation:** We had a customer-facing document Q&A feature in production for a large insurance client. Three months after launch, a customer escalated: the system had returned a confident, detailed answer to a regulatory question that was factually wrong — it had hallucinated a policy exception that didn't exist in any document.
>
> **Task:** Understand what happened, fix it, and prevent recurrence. I led the incident response.
>
> **Action:** Detection had been the first failure — we had no mechanism for the system to express uncertainty, and we had no monitoring on answer faithfulness in production. We only heard about it via a support ticket.
>
> Diagnosis via LangSmith: the retrieved chunks were from two different documents with slightly different policy language. The model synthesized them into a plausible-but-wrong answer. The retrieval step had pulled the wrong document because of a metadata filtering bug that allowed cross-client document bleed.
>
> Immediate fix: patched the metadata filter within two hours, deployed to production. Medium-term fix: added a faithfulness check — a secondary LLM call that scores whether the answer is grounded in the retrieved context — for every response above a certain stakes threshold. Answers below 0.8 faithfulness surface a disclaimer to the user. Longer-term: built a nightly eval pipeline measuring faithfulness on a golden Q&A set.
>
> **Result:** We disclosed the incident to the customer, explained what happened, and walked them through the safeguards we added. They stayed with us. In the following six months, our faithfulness score on the golden set went from unmeasured to a tracked 0.94. The incident was painful, but it forced us to build the observability we should have had at launch.

---

**Q: "How do you communicate AI risk or uncertainty to non-technical stakeholders?"**

> **Situation:** We were three weeks from launching an AI-powered tenant risk scoring feature — predicting likelihood of lease default based on payment history and application data. The VP of Product and the Chief Revenue Officer were excited and had already included it in customer conversations. My team had found that the model had a statistically significant accuracy gap across racial demographic proxies — zip codes that correlated with race showed different false positive rates.
>
> **Task:** Communicate this clearly to the VP and CRO, recommend a path forward, and not kill the feature or the relationship.
>
> **Action:** I asked for a 30-minute meeting and prepared a one-page brief — not a slide deck. The brief had three sections: what we found, what it means legally (Fair Housing Act exposure, potential for disparate impact claims), and three options with tradeoffs.
>
> Option A: ship as-is, accept the risk. Option B: delay and retrain with fairness constraints — adds 6-8 weeks but reduces the legal exposure significantly. Option C: ship a version that excludes the features driving the demographic disparity, with a clear roadmap to Option B.
>
> I didn't editorialize in the brief. I presented the numbers — differential false positive rates by zip code cluster — and let the business leaders make the call with full information.
>
> **Result:** They chose Option C, which I'd recommended as the pragmatic middle ground. The CRO called the conversation "the most mature AI risk briefing I've seen from an engineering team." The feature launched six weeks later without the problematic features, with a clear improvement roadmap. We avoided a fair housing audit. The brief format — problem, legal context, options with tradeoffs — became our standard template for AI risk escalations.

---

**Q: "Describe how you've built standards or best practices for an AI team."**

> **Situation:** After our team grew from 3 to 8 AI engineers in eight months, we had four different patterns for how prompts were written, three different approaches to evaluation, no common tracing setup, and two engineers who had never heard of prompt injection. Every PR review was a re-litigating of basic decisions.
>
> **Task:** I proposed and owned an AI engineering standards initiative. I had no budget and no dedicated time — this had to happen alongside normal delivery work.
>
> **Action:** I spent two weeks collecting the most common review comments from the past three months, clustering them into themes: prompt structure, eval coverage, observability, safety. That gave me a prioritized list that was grounded in real friction, not my preferences.
>
> I wrote four one-page standards — prompt design, eval requirements, tracing setup, safety checklist — each with examples from our codebase, not from textbooks. The safety checklist became a PR gate: no LLM-touching PR merged without checking for prompt injection surface, PII handling, and output validation. I added it to our GitHub PR template.
>
> For prompt versioning: I introduced a `prompts/` directory with YAML files — version, changelog, evaluation result. Prompts became config, not code. Changing a prompt without bumping the version and running the eval script became a blocking review comment.
>
> **Result:** Six months later, PR review time for AI components dropped from an average of 3.5 rounds to 1.8 rounds. Two engineers told me independently that the safety checklist had caught issues they'd have shipped. One of the four standards was adopted by an adjacent team that had similar problems. The pattern I learned: standards that come from real pain points get adopted; standards that come from an architect's preferences get ignored.

---

**Q: "Tell me about identifying a high-value AI opportunity that wasn't on the roadmap."**

> **Situation:** I was reviewing our customer support ticket data — not as part of any assigned work, just to understand user behavior better. I noticed that 34% of support tickets from property managers were asking questions that were already answered in our documentation or in data available in our system — 'what's the current lease renewal rate for property X?', 'which vendors are approved for HVAC work?'.
>
> **Task:** I had about a week to build a case before the next quarterly planning cycle closed.
>
> **Action:** I pulled a sample of 200 tickets and manually classified them: genuinely novel support need vs. could have been self-served with an AI-powered answer layer. 34% fell into the self-serve bucket. At our support cost of approximately $18 per ticket and 2,400 tickets per month, that was a $14,000/month opportunity — with a realistic expectation of deflecting 60-70% of that category.
>
> I built a one-page brief: the data, the opportunity size, a sketch of the architecture (RAG over documentation + system data, surfaced as a Slack bot and in-app widget), a rough engineering estimate (6 weeks for MVP), and a success metric — support ticket volume in the self-serve category, measured monthly.
>
> I presented it to the VP of Product as 'here's something I noticed and built a case for' rather than 'add this to the roadmap.' I offered to own the first sprint personally to de-risk it.
>
> **Result:** It made it into the next quarter's roadmap. We shipped the MVP in seven weeks. In the first three months, it deflected 58% of the self-serve ticket category — roughly $8,000/month in support cost savings. It also surfaced a documentation gap we hadn't known about because the AI's failure mode on certain questions made the missing docs visible.

---

**Q: "How have you handled a situation where the AI solution wasn't technically feasible but stakeholders were committed to it?"**

> **Situation:** A VP had promised a large customer a real-time AI underwriting feature — instantaneous credit risk assessment during the lease application flow. The customer had signed expecting a 500ms response time. When I dug into the requirements, the model they wanted would take 4-6 seconds on the current infrastructure, and the data pipeline required for real-time features didn't exist yet.
>
> **Task:** Tell the VP — who had already committed to the customer — that the feature as scoped couldn't be delivered. Without destroying the relationship or the customer deal.
>
> **Action:** I didn't go to the VP with a problem. I went with three options and a recommendation.
>
> Option A: Ship the feature at 4-6 seconds — technically feasible but violates the customer's stated requirement. Honest, but likely to damage trust.
>
> Option B: Build the real-time data pipeline first — technically correct, but 14 additional weeks, missing the customer timeline.
>
> Option C — my recommendation: ship a 'near real-time' version. Run the model asynchronously in the background the moment an application starts, so by the time the applicant reaches the underwriting step (typically 3-5 minutes later), the result is ready. The customer sees an instant result. The reality is a 6-second model run that completes well before they need it. We'd disclose this as 'asynchronous pre-computation' in the technical spec, not market it as real-time AI.
>
> I walked the VP through all three options in a 20-minute conversation, with the engineering tradeoffs and risks explicit.
>
> **Result:** The VP chose Option C and brought me into the follow-up conversation with the customer's technical team to explain the approach. The customer accepted it. We shipped on the original timeline. Six months later, we built the actual real-time pipeline and upgraded the feature — but by then the customer was already satisfied with the working product. The principle: never bring a VP a problem without options. And never overcommit on latency without checking the architecture.

---

## 4. PropTech & RealPage Domain Knowledge

| Area | What to Know | Where to Learn |
|------|-------------|----------------|
| **RealPage products** | AI Revenue Management (rent pricing), Spend Management, Leasing & Marketing AI, Renter Intelligence, OpsTechnology (maintenance) | RealPage.com product pages, press releases |
| **Property management workflow** | Lease lifecycle (prospect → application → screening → lease → renewal → move-out), maintenance work order flow, owner reporting cycle, compliance audit cycles | National Apartment Association (NAA) resources |
| **PropTech AI use cases** | Dynamic rent pricing, predictive maintenance, fraud detection in applications, chatbots for leasing, document extraction from leases, compliance monitoring | PropTech news (The Real Deal, Bisnow PropTech), RealPage blog |
| **Regulatory landscape** | Fair Housing Act (federal), HUD guidelines, GDPR (if EU tenants), CCPA (California), rent control laws, ADA digital accessibility, data residency requirements for tenant PII | HUD.gov, NCRC fair housing resources |
| **RealPage history** | Founded 1998, acquired by Thoma Bravo (private equity) in 2021 for $10.2B, DOJ antitrust investigation into AI rent pricing (2024), major enterprise SaaS player in multifamily | Wikipedia, news coverage |
| **Competitive landscape** | Yardi, MRI Software, AppFolio, Entrata — know how RealPage differentiates on AI | RealPage vs. competitors comparison articles |
| **AI rent pricing controversy** | DOJ/state AGs investigating algorithmic rent pricing — understand the responsible AI and governance angle, be ready to discuss | ProPublica "Secret Algorithm" article (2022), news coverage |

---

## 5. Questions to Ask the Interviewer

These show strategic thinking and genuine curiosity. Pick 3-5 per interview round.

| Question | What It Shows |
|----------|--------------|
| "What does the current AI evaluation framework look like — do teams have standardized metrics for relevance and safety, or is each team building their own?" | You think about platform and standards, not just features |
| "Where does the Agentic AI team sit relative to product teams — are you embedded, centralized, or a hybrid?" | You understand the organizational dynamics that determine AI team impact |
| "What's the biggest technical risk in the current AI architecture that you'd want the new Lead Engineer to address first?" | Direct, practical, shows you're ready to contribute immediately |
| "How does RealPage approach the responsible AI challenge around algorithmic rent pricing — is there an internal governance process?" | Shows domain awareness and ethical maturity, acknowledges the elephant in the room |
| "What does the model evaluation process look like today — is there a human annotation pipeline, or is it primarily automated?" | Shows eval framework thinking |
| "What's the ratio of greenfield AI work vs. integrating AI into existing systems?" | Practical — helps you understand what the actual day-to-day is |
| "How do you think about vendor lock-in with LLM providers — is there an OpenAI/Anthropic/Google strategy, or provider-agnostic?" | Shows you think about architectural durability |
| "What does a successful first 90 days look like for this role?" | Shows you're focused on outcomes, not just starting |

---

## 6. Coding / Live Assessment Preparation

If there is a technical screen or live coding component:

| Likely Task | How to Prepare |
|-------------|---------------|
| **Build a simple RAG pipeline** | Practice: `httpx` or `openai` + FAISS or chromadb + a simple chunker. Should take < 30 min. Know how to add reranking | 
| **Implement a tool-calling agent loop** | Practice: Anthropic/OpenAI tool_use loop from scratch — no LangChain. Define 2-3 tools, execute them, handle multi-turn. Should be fluent | 
| **Write a BM25 or TF-IDF search function** | Know the BM25 formula: IDF × TF-normalized by doc length. Practice implementing it in pure Python | 
| **Design a prompt for structured extraction** | Practice: take a prose document, write a system prompt + tool schema to extract structured data. Know when to use tool_choice vs. JSON mode | 
| **Debug a broken agent that loops** | Know common failure modes: missing stop condition, tool error not handled, context window overflow, ambiguous tool descriptions |
| **SQL/Cypher for graph queries** | Practice multi-hop Cypher: `MATCH (a)-[r*1..3]-(b)`, shortest path, `OPTIONAL MATCH`, `collect()`, `WITH` chaining |

---

## 7. Day-Before & Day-Of Checklist

| Task | Timing | Notes |
|------|--------|-------|
| Research your interviewers on LinkedIn | Day before | Look for their background — ML, engineering, product — tailor your examples |
| Read RealPage's most recent AI press releases | Day before | Know what products they're publicly launching or enhancing |
| Re-read the JD word for word | Day before | Map each responsibility to a story or project you can cite |
| Rehearse the project demo out loud (not in your head) | Day before | Time yourself — stay under 10 minutes for the project overview |
| Prepare your "why RealPage" answer | Day before | Be specific: PropTech domain, scale, the governance challenge, building a team |
| Test your setup if virtual | Morning of | Camera, mic, screen share, browser tabs pre-loaded |
| Restate each question before answering | During | Buys thinking time, ensures you answered what was asked |
| Have DESIGN_DECISIONS.md and INTERVIEW_PREP.md open | During (virtual) | Quick reference for architecture rationale if asked |
| Send a thank-you note within 2 hours | After | Reference one specific technical topic from the conversation |

---

## 8. Compensation & Negotiation Preparation

| Item | Guidance |
|------|---------|
| **Market rate for Lead AI Engineer** | $220k–$320k base in Texas/remote depending on experience level and scope; total comp with bonus/equity $280k–$420k. RealPage is PE-backed (Thoma Bravo) so equity may be limited relative to FAANG |
| **Levels to clarify** | Is this an IC Lead (individual contributor) or a people manager? How many directs? Budget ownership? These change comp significantly |
| **Competing offer leverage** | If you have another offer, use it. If not, cite market data (Levels.fyi, Glassdoor for AI roles) and your specific impact |
| **Questions to ask about comp** | "What does the total comp structure look like — base, bonus target, equity?" / "Is equity in the parent company (Thoma Bravo portfolio) or RealPage?" |
| **Non-monetary terms to negotiate** | Remote flexibility (2-3 days in office is stated — clarify which days), conference budget, learning budget, title (Staff vs. Lead vs. Principal), team size and hiring authority |

---

## 9. Red Flags to Watch For

| Signal | What It Might Mean |
|--------|--------------------|
| "We're just starting our AI journey" | You may be building from scratch with limited infrastructure — clarify scope and resources |
| No mention of evaluation frameworks or responsible AI in interviews | Culture may be shipping-first without quality guardrails — ask explicitly |
| Vague answers about the DOJ/pricing investigation | May indicate the org is not comfortable discussing AI governance — a risk for a Lead role that includes responsible AI |
| Interview panel has no current AI/LLM practitioners | Role may be more about vision-setting than hands-on building |
| "We use LangChain for everything" | May indicate a team that followed trends rather than building foundational understanding |
| Pressure to commit to unrealistic timelines | Lead AI roles need room to build infrastructure correctly — understand expectations |
