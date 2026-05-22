# CogniGraph — 2-Minute Demo Script

**Format:** Screen recording with voiceover  
**Pace:** ~140 words/min · ~280 words spoken · remaining time = UI action pauses  
**Tone:** Conversational, live-demo energy — not a product pitch, more like showing a colleague something cool  
**Keywords:** Bolded inline — emphasize these words slightly when speaking. They're the signal words a technical audience picks up on.

---

## [0:00 – 0:08] Hook

> *Open on the Source tab — pipeline banner visible, document beginning to render.*

"
Hi evryone,
a quick pre text.
I did similar project for my current employer and this is an open-source conceptual replica.
Company knowledge lives in documents. Our Solution says: 
what if you just… gave that document to an AI, and got a live **knowledge graph** back?"

---

## [0:08 – 0:35] The Origin Story — Source Tab

> *Source tab fully visible. Pipeline banner: nexus_corp_brief.md → Claude Opus → 30 nodes · 73 rels.*

"This is the source. A plain-text company brief — the kind of thing that already exists in any company's wiki. We passed it to an LLM with one **structured tool call** — so LLM return a single, schema-validated response."

> *Scroll slowly down the document — highlighted entity names glow in their colors.*

"Look at what happened. It read the prose, pulled out the structure, and wrote it straight into **Neo4j** as **typed relationships**."

> *Pause on a dense paragraph — multiple colored highlights visible at once.*

"There is No schema defined up front. No manual data entry. **Document in, knowledge graph out.**"

---

## [0:35 – 0:55] The Graph — Explore

> *Switch to Graph tab. Simulation has settled, particles flowing along edges.*

"Here's that graph. Thirty nodes, seventy-three **typed relationships** — 
the **force-directed simulation** finds the clusters on its own. 
Particles on each edge show direction of the relationship."

> *Click on a Person node — panel slides in smoothly.*

"Click any node. You get properties, every connection in and out, and a **three-hop impact analysis** — 
so if Priya left tomorrow, what breaks downstream? It traces the whole chain."

---

## [1:08 – 1:48] Query — Streaming Chat with Human Review

> *Switch to Query tab. Sidebar shows sample queries on the left.*

"Now the interesting part.  You can ask Cross-Fucntional complex queries. Every query sends the full graph as a **cached system prompt**."

> *Tokens begin streaming in via SSE.*

"Watch it reason. Person — works on — product — used by — customer. **Multi-hop reasoning** across **typed relationships**, grounded in real graph data. This is **SSE streaming** — tokens arrive the moment they're generated."

> *Response finishes. Review controls appear below the answer.*

"Another critical aspect of this workflow: **Human Review**, built into the response itself. 

> *Click thumbs down — inline comment form opens.*

"Flag it. Add context about what was wrong."

> *Type a short comment, submit — sidebar auto-switches to Review tab.*

"It lands in the **Review panel**. Every flagged response in one place — **closed-loop human review**, ready to feed back into prompt or model improvement."

---

## [1:48 – 2:00] Close

> *Return to Graph tab. Full graph, particles flowing.*

"
Here are the Key takeaways.
with a document. 
You can get a **queryable knowledge graph** with **streaming LLM** on top, 
**human review** built in, 
and package it as an **MCP server** for agentic interface — all on the stack you can run locally in under a minute."

*"All source. Start with `python api.py`."*

---

**Total spoken words:** ~340 (slightly over 2:00 with fast delivery — trim the stack section if needed)

**Key beats to hit on screen:**

| Time | Action |
|------|--------|
| 0:00 | Source tab open — pipeline banner + document rendering |
| 0:15 | Scroll document slowly — highlights visible |
| 0:28 | Pause on dense highlighted paragraph |
| 0:35 | Switch to Graph tab |
| 0:42 | Click a Person node → panel slides in |
| 0:50 | Click neighbor node from within panel |
| 0:55 | Cut to architecture diagram or repo file tree |
| 1:00 | Hold on diagram — layers visible |
| 1:08 | Switch to Query tab |
| 1:14 | Click sidebar suggestion |
| 1:17 | Watch tokens stream in |
| 1:36 | Click thumbs down → comment form opens |
| 1:40 | Type comment, submit → Review tab auto-selects |
| 1:48 | Return to Graph tab |

---

## Technical Keywords Reference

> Quick-scan before recording. These are the terms that signal depth to a technical audience — make sure each one lands clearly at least once.

**Data & Graph**
- `Knowledge graph` — use this, not just "graph"
- `Typed relationships` — Neo4j's core value prop
- `Entity extraction` — what Claude Opus does to the document
- `Three-hop impact analysis` — the panel's killer feature
- `Cypher` — mention it to show you know the query layer exists
- `Force-directed simulation` — name the physics model

**LLM & AI**
- `Structured tool call` / `tool_choice: forced` — shows deliberate LLM design
- `Prompt caching` — the cost efficiency story
- `Cached system prompt` — specifically how the graph is pinned
- `Multi-hop reasoning` — what the query answer demonstrates
- `SSE streaming` — Server-Sent Events, tokens arrive live
- `Graph fits in context` — no RAG needed at this scale

**Infrastructure**
- `Neo4j` — named, not just "graph database"
- `FastAPI` — async Python API layer
- `D3 canvas` — react-force-graph-2d under the hood
- `MCP server` / `stdio` — Model Context Protocol, agentic surface
- `Vite dev proxy` — zero CORS friction (optional, only if showing code)

**Product**
- `Human-in-the-loop` — the review feature's positioning
- `Closed-loop feedback` — flagged responses → review panel
- `Document in, knowledge graph out` — the one-liner for the origin story

---

**Delivery notes:**

- *"Document in, knowledge graph out."* — say it like a slogan. Full stop after it.
- *"just — a document, and then a graph"* — pause before "a document". Let the silence do work.
- Stack section — read it fast, like rattling off ingredients. The diagram is doing the explaining.
- *"Watch it reason."* — say this right as the first token appears. Timing is everything.
- *"Closed loop."* — two words, drop pitch, full stop. Don't add anything after it.
- The close is intentionally abrupt. End on the graph, not on a pitch.
