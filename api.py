import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel
from anthropic import AsyncAnthropic
from models import NodeCreate, RelationshipCreate
import graph as g

_anthropic = AsyncAnthropic()

SYSTEM_PROMPT = """You are an intelligent analyst for Nexus Corp, a fictional B2B SaaS company. \
You have access to the company's complete knowledge graph, which includes people, products, customers, \
workflows, and decisions along with all their relationships.

Node types:
- Person: employees with roles (Engineering, Sales, Design, Leadership, etc.)
- Product: software products (platform, module, add-on, etc.)
- Customer: companies using Nexus Corp products
- Workflow: internal processes and operational procedures
- Decision: strategic decisions made by leadership

Relationship types: WORKS_ON, OWNS, MADE, INVOLVES, PRODUCES, DEPENDS_ON, USES, AFFECTS, REPORTS_TO, \
MANAGES, LEADS, ASSIGNED_TO, REQUIRES, BLOCKS, SUPPORTS, INFLUENCES

Answer questions about the organization, its people, products, customers, workflows, and decisions. \
Be specific, cite node names and relationships from the graph data, and reason across multiple hops \
when needed. Format your answers clearly with structure when appropriate."""

app = FastAPI(title="Company Knowledge Graph API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/")
def health():
    return {"status": "ok", "stats": g.graph_stats()}


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
def list_nodes(type: str = Query(None, description="Filter by label: Person, Product, Customer, Workflow, Decision"),
               limit: int = Query(100, ge=1, le=500)):
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
def search(q: str = Query(..., min_length=1), type: str = Query(None)):
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
        """
        MATCH (n {id: $id})-[r*1..3]-(m)
        WHERE m.id <> $id
        RETURN DISTINCT m, size(r) AS hops
        ORDER BY hops
        """,
        {"id": node_id},
    )
    return {
        "source": node,
        "reachable": [{"node": g.node_dict(r["m"]), "hops": r["hops"]} for r in rows],
    }


class QueryRequest(BaseModel):
    question: str


def _format_graph(graph: dict) -> str:
    lines = ["=== NODES ==="]
    for n in graph["nodes"]:
        props = {k: v for k, v in n.items() if k not in ("id", "label", "_labels")}
        lines.append(f"[{n['label']}] id={n['id']} | " + " | ".join(f"{k}={v}" for k, v in props.items() if v))
    lines.append("\n=== RELATIONSHIPS ===")
    for r in graph["relationships"]:
        lines.append(f"{r['from_id']} --[{r['type']}]--> {r['to_id']}")
    return "\n".join(lines)


@app.post("/query")
async def query_graph(body: QueryRequest):
    if not body.question.strip():
        raise HTTPException(422, "question must not be empty")

    graph = g.get_full_graph()
    graph_context = _format_graph(graph)

    search_hits = g.search_nodes(body.question)
    search_text = (
        "Keyword search results for your query:\n"
        + "\n".join(f"- [{h['label']}] {h.get('name', h['id'])}" for h in search_hits)
        if search_hits else "No direct keyword matches found."
    )

    async def event_stream():
        try:
            async with _anthropic.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": f"Full knowledge graph data:\n\n{graph_context}",
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
                    yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


if __name__ == "__main__":
    import uvicorn
    from seed import seed
    seed()
    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"), port=int(os.getenv("API_PORT", 8000)))
