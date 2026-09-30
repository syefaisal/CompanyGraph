# Knowledge Graph Implementation Plan

Sep 30, 2026 · @syfai

## Overview

The goal is to ship two graph-backed agents in about 24 weeks: an Incident Impact/RCA agent and a Release Risk agent. The Incident agent comes first. It needs less data, and past incidents give you ready-made test cases.

Principles that hold across every phase:

- **Questions before schema.** Every node and edge must serve a written question an agent needs answered.
- **Test gates, not dates.** A phase ends when its exit tests pass. If a gate fails, fix it before moving on.
- **Backtest on history.** Past incidents and releases with known outcomes are your ground truth. Build that dataset early.
- **Thin vertical slices.** Take one product line end to end before going wide across the estate.
- **Advisory before blocking.** Agents run in shadow mode before their output influences any real decision.

| Phase | Focus | Weeks | Exit gate |
| --- | --- | --- | --- |
| 0 | Discovery and stakeholders | 1–3 | Source inventory and sponsor sign-off |
| 1 | Foundations | 3–5 | Golden dataset of 30+ incidents, competency questions agreed |
| 2 | Topology + changes + incidents | 5–10 | Entity resolution ≥ 90% precise; graph answers 10 golden questions |
| 3 | Customer impact | 10–13 | Impacted-customer lists match support records ≥ 85% |
| 4 | RCA extraction + retrieval | 13–17 | Root-cause labels ≥ 80% correct; similar-incident recall@5 ≥ 70% |
| 5 | Agents | 17–24 | RCA top-3 hit rate ≥ 60% on backtest; risk score separates bad releases |
| 6 | Shadow mode + rollout | 24+ | Engineers rate output useful ≥ 70% of the time |

The thresholds above are starting targets. Recalibrate them once you see your baseline in Phase 1.

## Phase 0: Discovery (weeks 1–3)

As a new hire, your first job is to learn how incidents and releases actually work here. That is often different from how the docs say they work. Build credibility by producing useful artifacts, not by writing code.

1. **Find a sponsor and two champions.** The sponsor is usually the head of SRE, Ops or Release Engineering. The champions are one senior SRE and one release or change manager who feel the pain daily.
2. **Interview 8–12 people.** Cover incident commanders, SREs, release managers, CMDB owners, the Salesforce admin, support leads and a product owner. Ask each of them:
   - Walk me through the last bad incident. How did you find the cause, and how long did it take?
   - How do you decide a release is risky today?
   - Which data source do you trust least, and why?
3. **Inventory every source.** For Salesforce, CMDB, TFS and the RCA repository, record the owner, access method (API, export, DB replica), refresh rate, volume, key fields and known quality issues.
4. **Trace three real incidents by hand.** Follow each one across every system. Note where IDs link cleanly, where they break, and where a human had to guess. This will be your first real look at the entity resolution problem.
5. **Request access early.** Read-only API credentials and security review can take weeks.
6. **Write a two-page proposal.** State the problem, the two agents, the phased plan and the success metrics. Get sign-off from your sponsor.

**Deliverables:** source inventory, three incident traces, stakeholder map, signed-off proposal.

**Exit test:** your sponsor agrees on the success metrics, and read access to at least CMDB, TFS and incident data is approved.

## Phase 1: Foundations (weeks 3–5)

Build the test harness before you build the graph. Everything later is measured against what you produce here.

1. **Write the competency questions.** Aim for 15–20 per agent, reviewed with your champions. Each one should be concrete enough to answer by hand, for example: "Which customers were affected by the incident on the payments API last March?"
2. **Build the golden dataset.** With your SRE champion, take 30–50 past incidents that have a completed RCA and record, for each one:
   - the true root cause, including the causing change request if there was one
   - the affected services and CIs
   - the impacted customers
   - how long diagnosis took (your baseline)
3. **Build a release outcome set.** Take 100+ past releases and change requests, each labeled as caused an incident within 7 days (yes or no). Most will be clean. That imbalance is normal.
4. **Draft the root-cause taxonomy.** Start with 10–15 categories built from existing RCAs (for example: bad deploy, config drift, capacity, dependency failure, certificate or secret expiry, data issue). Have SREs review it.
5. **Pick the stack.** A reasonable default:
   - Graph: Neo4j (vector index included)
   - Staging: Postgres or your existing lakehouse
   - Orchestration: Airflow, Prefect or ADF
   - Agents: LangGraph
   - Tracing and evaluation: Langfuse or LangSmith
6. **Draft schema v1.** Cover only the node and edge types your competency questions need. Version it in Git.

**Deliverables:** competency questions, golden incident set, release outcome set, taxonomy v1, schema v1, dev environment.

**Exit test:** every competency question maps to a traversal in schema v1, and the golden set covers at least three product lines.

## Phase 2: Core graph — topology, changes, incidents (weeks 5–10)

This phase produces the smallest graph that can answer "what changed upstream of this incident?" Start with one product line, then expand.

1. **Load the CMDB topology.** Load products, services, components, infrastructure CIs and environments, with `DEPENDS_ON`, `RUNS_ON` and `OWNS` edges. Add `valid_from` and `valid_to` on edges from the start. Retrofitting time later is painful.
2. **Build the entity resolution service.** Create a canonical ID table plus an alias table (source system, source key, canonical ID, method, confidence). Match in this order:
   1. exact keys
   2. normalized names
   3. rules (for example, TFS area path to service)
   4. LLM-assisted fuzzy matching
   5. human review queue for anything below the confidence threshold
3. **Load TFS change requests.** Load CRs, releases and deployments with `MODIFIES` and `DEPLOYED_TO` edges and timestamps. CRs that touch no resolvable CI are a data-quality metric. Track that count.
4. **Load incidents.** Load them from Salesforce (or your ITSM tool) with `AFFECTED` edges to CIs. Load severity and start and end times.
5. **Make pipelines idempotent.** Upsert by canonical ID, run daily at first, and log every run with row counts and rejects.
6. **Write the first 5 graph queries by hand in Cypher:** blast radius, upstream path, changes on the upstream path within a time window, incident history per CI, and change collisions.
7. **Add observed topology (optional but valuable).** If APM or tracing exists, load observed `CALLS` edges and diff them against the CMDB.

**Deliverables:** running pipelines, entity resolution service with review queue, 5 tested Cypher queries, data-quality dashboard.

**Exit test:** see Testing strategy levels 1–3. In short, entity resolution precision ≥ 90%, and the causing CR appears in "changes on upstream path" for at least 60% of golden incidents that were change-caused.

## Phase 3: Customer impact layer (weeks 10–13)

This phase connects customers to what they run on, so every blast radius can be weighted by business impact.

1. **Load from Salesforce:** accounts, contracts (SLA tier, ARR band), subscribed products and features, and support cases linked to incidents.
2. **Resolve the customer-to-infrastructure mapping.** This is usually the weakest link. Customers often map to a tenant, region or environment rather than directly to a service. Work with the platform team to find the source of truth, which may be a tenant registry rather than Salesforce.
3. **Add a customer exposure query.** Given a set of CIs, return impacted customers with tier and ARR, ranked by exposure.
4. **Handle sensitivity.** Customer and contract data needs access controls. Agree with security on who can see ARR, and consider exposing tiers or bands instead of raw numbers.

**Deliverables:** customer subgraph, tenant mapping, exposure query, access-control design.

**Exit test:** for golden incidents, the graph's impacted-customer list matches the customers who actually opened cases or received notices at ≥ 85% recall. False positives are acceptable at this stage, because they represent customers who were exposed.

## Phase 4: RCA extraction and hybrid retrieval (weeks 13–17)

This phase turns RCA documents into structured, linked knowledge, so agents can learn from past incidents.

1. **Build the extraction pipeline.** An LLM with a strict JSON schema extracts from each RCA:
   - affected CIs
   - root cause (taxonomy code)
   - causing change, if any
   - contributing factors
   - detection gap
   - action items with owner and status
2. **Resolve every extracted entity** through the Phase 2 entity resolution service. Never create a new node from free text without resolving it first.
3. **Store provenance on every edge:** source document, extraction model version, confidence.
4. **Chunk and embed the RCA text.** Link each chunk to its RCA and Incident nodes, then add Neo4j vector indexes.
5. **Build similar-incident retrieval** as a hybrid query:
   1. filter by shared or neighboring CIs in the graph
   2. rank by embedding similarity
   3. boost results with the same taxonomy code
6. **Route low-confidence extractions to SRE review.** Corrections become labeled data for improving the prompts.

**Deliverables:** extraction pipeline, embedded RCA corpus, similar-incident query, review workflow.

**Exit test:** on a hand-labeled sample of 30 RCAs, root-cause code accuracy is ≥ 80% and CI extraction F1 is ≥ 0.8. On the golden set, recall@5 for similar incidents is ≥ 70%, measured against the incidents SREs say are similar.

## Phase 5: Agents (weeks 17–24)

Wrap the graph in tested tools first, then build the Incident agent, then the Release Risk agent.

**Step 1: graph tool layer (weeks 17–18).** Expose 8–12 parameterized functions as LangGraph tools:

- `get_blast_radius`
- `changes_on_upstream_path`
- `similar_incidents`
- `customer_exposure`
- `ci_incident_history`
- `change_collisions`
- `open_action_items`

Each tool gets unit tests against a fixture graph. Add a read-only, timeout-bounded text-to-Cypher tool only as a fallback.

**Step 2: Incident Impact/RCA agent (weeks 18–21).** The flow:

1. anchor on the affected CIs
2. find downstream impact and customer exposure
3. find upstream candidates and recent changes on those paths
4. find similar past incidents
5. return ranked root-cause hypotheses, each with its evidence path

Keep the ranking partly deterministic, using change recency, graph distance and similar-incident votes. The LLM narrates and adjudicates; it does not invent causes.

**Step 3: Release Risk agent (weeks 21–24).** For a given CR, compute these features:

- blast radius weighted by customer tier
- historical change failure rate of the touched CIs
- recent incident count on those CIs
- open action items
- change collisions
- change size and timing

Start with a transparent weighted score. Move to a simple model (logistic regression or gradient boosting) only once you have enough labeled outcomes. The LLM writes the explanation and cites the graph paths.

**Step 4: observability.** Trace every agent run: tool calls, latency, tokens, and the final answer, stored for evaluation.

## Phase 6: Shadow mode, feedback loop, rollout (week 24+)

Earn trust in live conditions before the agents influence real decisions.

1. **Shadow mode, 4–6 weeks.** Agents run on every real incident and CR, but their output goes to a private channel read by your champions only. Nobody acts on it.
2. **Capture feedback in one click.** Ask "Was the top hypothesis right? Useful / not useful." For releases, record whether the CR later caused an incident.
3. **Write confirmed outcomes back to the graph.** Add `CAUSED_BY {source: "human", confidence: 1.0}`, and add release outcomes to the release outcome set. The graph and the backtest set grow together.
4. **Advisory mode.** Post agent output into the incident channel and the CAB/change review, clearly labeled as advisory.
5. **Gated mode (optional, later).** Only high risk scores trigger extra review, and never an automatic block without a human.
6. **Expand coverage** to further product lines, repeating the Phase 2–4 exit tests for each.

**Exit test:** see Testing strategy levels 6–7.

## Testing strategy

Test at seven levels, from the raw data up to business outcomes. Lower levels run automatically on every pipeline run or build. Higher levels run at phase gates and then weekly.

| Level | What it proves | How to test | Target | When |
| --- | --- | --- | --- | --- |
| 1. Data quality | Sources loaded completely and correctly | Row-count reconciliation vs. source; null and format checks on key fields; freshness checks (Great Expectations or dbt tests) | Row counts match within 1%; data fresher than 24 h | Every pipeline run |
| 2. Entity resolution | IDs across systems point to the right thing | Hand-label 200 random alias matches; measure precision and recall; track unresolved rate per source | Precision ≥ 90%, recall ≥ 80%, unresolved < 10% | Phase 2 gate, then monthly |
| 3. Graph correctness | The graph reflects reality | Schema constraints; orphan-node checks; SMEs verify dependency chains for 20 services; CMDB vs. observed-topology diff; golden competency questions return expected answers | 0 constraint violations; SME agreement ≥ 90%; golden questions pass | Every load, plus phase gates |
| 4. Tools and retrieval | Each graph tool returns the right results | Unit tests on a fixture graph with known answers; similar-incident recall@5; causing-CR hit rate on the upstream-changes query | All unit tests pass; recall@5 ≥ 70%; CR hit ≥ 60% | Every build (CI) |
| 5. Agent backtest | Agents reach the right conclusions on history | Replay golden incidents with the graph as-of the incident time (hide later data); score top-1 and top-3 root-cause accuracy, impact recall, faithfulness of cited evidence (LLM-as-judge plus spot checks). For releases: AUC/precision of risk score on the release outcome set | RCA top-3 ≥ 60%; risk AUC ≥ 0.7; 0 fabricated evidence paths | Every prompt, model or tool change |
| 6. Shadow mode | Agents help on live, unseen events | Compare agent output against the eventual human RCA and release outcomes; track engineer ratings | Top-3 hit ≥ 60% live; useful rating ≥ 70% | Weekly during shadow |
| 7. Business outcomes | The system is worth it | Before/after comparison against the Phase 1 baseline | MTTD/diagnosis time down 20–30%; change failure rate down; fewer Sev1s from risky releases | Quarterly |

**Test habits that matter most:**

- **Prevent time leakage.** In backtests, the agent must only see data that existed at the incident or release time. Otherwise the RCA document itself gives away the answer. Temporal edges from Phase 2 make this possible.
- **Freeze a regression suite.** Keep the golden set fixed and version it. Every change to prompts, models, schema or tools reruns it, and results are compared in Langfuse or LangSmith before merge.
- **Keep a held-out set.** Tune on 70% of the golden incidents and report on the other 30%, so you don't overfit prompts to cases you've seen.
- **Check evidence, not just answers.** A correct root cause with a fabricated path is a failure. Check that every cited node and edge exists in the graph.
- **Test with chaos.** Once the system is live, use game days or chaos experiments with known injected causes as additional labeled test cases.

## Risks and mitigations

| Risk | Early signal | Mitigation |
| --- | --- | --- |
| CMDB is stale or incomplete | SMEs reject dependency chains; many CRs don't resolve to CIs | Add observed topology from APM/traces; report gaps to CMDB owners as a byproduct |
| Entity resolution stalls | Review queue keeps growing | Narrow to one product line; get alias rules from owners; accept a lower threshold with confidence flags |
| Too few labeled incidents | Golden set < 30 | Include Sev2/Sev3 incidents; reconstruct labels with SREs; add game-day cases |
| Access delays | Credentials pending > 3 weeks | Start with exports; escalate through your sponsor |
| Agents sound confident but are wrong | Fabricated paths in backtest; low shadow ratings | Deterministic ranking; mandatory evidence paths; path-existence checks |
| Low adoption | Nobody reads shadow output | Deliver output where people already work (incident channel, CAB); involve champions in design |
| Scope creep | Requests for new sources or agents mid-build | Hold to phase gates; log requests for after Phase 6 |
