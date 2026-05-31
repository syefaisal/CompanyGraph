"""
Meridian Property Group — Knowledge Graph MCP Server

Exposes the Neo4j knowledge graph as MCP tools so any MCP-compatible AI
(Claude, etc.) can query people, products, customers, workflows, and decisions
for a PropTech SaaS company managing residential and commercial properties.

Run via stdio (Claude Desktop / Claude Code):
    python mcp_server.py

Or via MCP CLI:
    mcp run mcp_server.py
"""
import json
from mcp.server.fastmcp import FastMCP
import graph as g

mcp = FastMCP(
    "meridian-property-graph",
    instructions=(
        "You have access to Meridian Property Group's company knowledge graph. "
        "Meridian is a PropTech SaaS company providing lease management, "
        "maintenance, payment, and analytics software for property managers. "
        "The graph contains People (engineers, compliance, leasing, operations), "
        "Products (LeaseTrack, MaintenanceOS, TenantPay, OwnerInsight, LegacyPortal), "
        "Customers (residential and commercial property management firms), "
        "Workflows (Lease Renewal, Work Order Processing, Fair Housing Audit, etc.), "
        "and Decisions (deprecations, compliance overhauls, market expansions). "
        "Use these tools to answer questions about the company, trace decision impact, "
        "find single points of failure, understand compliance posture, and map "
        "customer-to-product relationships."
    ),
)

VALID_LABELS = {"Person", "Product", "Customer", "Workflow", "Decision"}
VALID_REL_TYPES = {
    "WORKS_ON", "OWNS", "MADE", "AFFECTS", "INVOLVES",
    "DEPENDS_ON", "PRODUCES", "USES",
}

# Use hybrid BM25 search by default; fall back to substring search if needed
_search = g.hybrid_search_nodes


def _fmt(data) -> str:
    return json.dumps(data, indent=2, default=str)


# ── Read tools ───────────────────────────────────────────────────────────────

@mcp.tool()
def list_entities(entity_type: str) -> str:
    """
    List all entities of a given type.

    Args:
        entity_type: One of Person, Product, Customer, Workflow, Decision
    """
    if entity_type not in VALID_LABELS:
        return f"Invalid entity_type. Choose from: {', '.join(sorted(VALID_LABELS))}"
    nodes = g.list_nodes(label=entity_type)  # list_entities always returns all; no search needed
    if not nodes:
        return f"No {entity_type} nodes found."
    lines = [f"Found {len(nodes)} {entity_type}(s):\n"]
    for n in nodes:
        props = {k: v for k, v in n.items() if k not in ("_labels", "created_at")}
        lines.append(f"  [{n['id']}] {n.get('name', '?')} — {_fmt(props)}")
    return "\n".join(lines)


@mcp.tool()
def get_entity(entity_id: str) -> str:
    """
    Get full details and all connections for a specific entity.

    Args:
        entity_id: The entity's id (e.g. 'p1', 'pr2', 'c3', 'w4', 'd5')
    """
    node = g.get_node_with_connections(entity_id)
    if not node:
        return f"No entity found with id '{entity_id}'."

    connections = node.pop("connections", [])
    result = [f"Entity: {node.get('name')} ({', '.join(node.get('_labels', []))})", _fmt(node)]

    if connections:
        result.append(f"\nConnections ({len(connections)}):")
        for c in connections:
            direction = "→" if c["direction"] == "out" else "←"
            result.append(
                f"  {direction} [{c['rel_type']}] {c['neighbor_name']} "
                f"({', '.join(c['neighbor_labels'])}) [id: {c['neighbor_id']}]"
            )
    else:
        result.append("\nNo connections found.")
    return "\n".join(result)


@mcp.tool()
def search_graph(keyword: str, entity_type: str = "") -> str:
    """
    Search for entities by name, role, description, or other text properties.

    Args:
        keyword: Text to search for (case-insensitive)
        entity_type: Optional filter — one of Person, Product, Customer, Workflow, Decision
    """
    label = entity_type if entity_type in VALID_LABELS else None
    results = _search(keyword=keyword, label=label)
    if not results:
        return f"No results for '{keyword}'" + (f" in {entity_type}" if label else "") + "."
    lines = [f"Found {len(results)} result(s) for '{keyword}':"]
    for n in results:
        lines.append(f"  [{n['id']}] {n.get('name')} ({', '.join(n.get('_labels', []))}) — {_fmt({k: v for k, v in n.items() if k not in ('_labels',)})}")
    return "\n".join(lines)


@mcp.tool()
def find_path(from_id: str, to_id: str) -> str:
    """
    Find the shortest connection path between any two entities in the graph.

    Args:
        from_id: Starting entity id
        to_id: Destination entity id
    """
    path = g.find_shortest_path(from_id, to_id)
    if path is None:
        return f"No path found between '{from_id}' and '{to_id}' (within 10 hops)."
    steps = []
    for step in path:
        if "node" in step:
            n = step["node"]
            steps.append(f"[{n['id']}] {n['name']} ({', '.join(n.get('labels', []))})")
        else:
            steps.append(f"  ──[{step['via']}]──▶")
    return "Path:\n" + "\n".join(steps)


@mcp.tool()
def trace_decision_impact(decision_id: str) -> str:
    """
    Trace everything a decision directly or indirectly affects — products,
    customers, workflows, and people.

    Args:
        decision_id: The decision's id (e.g. 'd1')
    """
    node = g.get_node(decision_id)
    if not node or "Decision" not in node.get("_labels", []):
        return f"No Decision found with id '{decision_id}'."

    rows = g.run(
        """
        MATCH (d:Decision {id: $id})-[r*1..3]-(m)
        WHERE m.id <> $id
        RETURN DISTINCT labels(m)[0] AS label, m.id AS id, m.name AS name,
               min(size(r)) AS hops
        ORDER BY hops, label
        """,
        {"id": decision_id},
    )
    lines = [
        f"Decision: {node.get('name')}",
        f"Rationale: {node.get('rationale', 'N/A')}",
        f"Date: {node.get('date', 'N/A')}",
        f"\nImpact chain ({len(rows)} entities):",
    ]
    for r in rows:
        lines.append(f"  hops={r['hops']}  [{r['label']}] {r['name']} (id: {r['id']})")
    return "\n".join(lines)


@mcp.tool()
def get_workflow_team(workflow_id: str) -> str:
    """
    Get all people involved in or owning a workflow.

    Args:
        workflow_id: The workflow's id (e.g. 'w1')
    """
    node = g.get_node(workflow_id)
    if not node or "Workflow" not in node.get("_labels", []):
        return f"No Workflow found with id '{workflow_id}'."

    rows = g.run(
        """
        MATCH (w:Workflow {id: $id})-[r]-(p:Person)
        RETURN p.id AS id, p.name AS name, p.role AS role,
               p.department AS dept, type(r) AS rel_type
        ORDER BY rel_type, name
        """,
        {"id": workflow_id},
    )
    lines = [f"Workflow: {node.get('name')}", f"Description: {node.get('description', 'N/A')}", ""]
    if not rows:
        lines.append("No people connected to this workflow.")
    else:
        lines.append(f"Team ({len(rows)} people):")
        for r in rows:
            lines.append(f"  [{r['rel_type']}] {r['name']} — {r['role']} ({r['dept']}) [id: {r['id']}]")
    return "\n".join(lines)


@mcp.tool()
def get_customer_products(customer_id: str) -> str:
    """
    Get all products a customer uses, plus the owner/engineering contacts for each.

    Args:
        customer_id: The customer's id (e.g. 'c1')
    """
    node = g.get_node(customer_id)
    if not node or "Customer" not in node.get("_labels", []):
        return f"No Customer found with id '{customer_id}'."

    rows = g.run(
        """
        MATCH (c:Customer {id: $id})-[:USES]->(pr:Product)
        OPTIONAL MATCH (p:Person)-[:WORKS_ON]->(pr)
        RETURN pr.id AS pr_id, pr.name AS pr_name, pr.status AS status,
               pr.version AS version, collect(p.name) AS engineers
        ORDER BY pr_name
        """,
        {"id": customer_id},
    )
    lines = [
        f"Customer: {node.get('name')} ({node.get('tier')} / {node.get('industry')})",
        f"ARR: ${node.get('arr_usd', 0):,}",
        "",
    ]
    if not rows:
        lines.append("No products found for this customer.")
    else:
        lines.append(f"Products in use ({len(rows)}):")
        for r in rows:
            lines.append(f"  [{r['pr_id']}] {r['pr_name']} v{r['version']} ({r['status']})")
            if r["engineers"]:
                lines.append(f"         Engineers: {', '.join(r['engineers'])}")
    return "\n".join(lines)


@mcp.tool()
def get_graph_summary() -> str:
    """
    Get a high-level summary of the knowledge graph — counts, key entities,
    and most-connected nodes.
    """
    stats = g.graph_stats()

    most_connected = g.run(
        """
        MATCH (n)-[r]-()
        RETURN n.name AS name, labels(n)[0] AS label, count(r) AS degree
        ORDER BY degree DESC LIMIT 10
        """
    )

    lines = [
        "=== Company Knowledge Graph Summary ===",
        "",
        "Node counts:",
        *[f"  {label}: {count}" for label, count in stats["nodes"].items()],
        f"  Total relationships: {stats['relationships']}",
        "",
        "Most connected entities:",
        *[f"  {r['name']} ({r['label']}) — {r['degree']} connections" for r in most_connected],
    ]
    return "\n".join(lines)


# ── Write tools ───────────────────────────────────────────────────────────────

@mcp.tool()
def add_entity(label: str, name: str, properties: str = "{}") -> str:
    """
    Add a new entity to the knowledge graph.

    Args:
        label: One of Person, Product, Customer, Workflow, Decision
        name: Display name for the entity
        properties: JSON string of additional properties (optional)
    """
    if label not in VALID_LABELS:
        return f"Invalid label. Choose from: {', '.join(sorted(VALID_LABELS))}"
    try:
        props = json.loads(properties)
    except json.JSONDecodeError:
        return "properties must be valid JSON, e.g. '{\"role\": \"Engineer\"}'"

    props["name"] = name
    node = g.create_node(label, props)
    return f"Created {label}: {name} [id: {node['id']}]"


@mcp.tool()
def connect_entities(from_id: str, to_id: str, relationship_type: str, properties: str = "{}") -> str:
    """
    Create a relationship between two existing entities.

    Args:
        from_id: Source entity id
        to_id: Target entity id
        relationship_type: One of WORKS_ON, OWNS, MADE, AFFECTS, INVOLVES, DEPENDS_ON, PRODUCES, USES
        properties: JSON string of relationship properties (optional)
    """
    rel = relationship_type.upper().replace(" ", "_")
    try:
        props = json.loads(properties)
    except json.JSONDecodeError:
        return "properties must be valid JSON."

    ok = g.create_relationship(from_id, to_id, rel, props)
    if not ok:
        return f"Failed: one or both IDs not found ('{from_id}', '{to_id}')."
    return f"Connected [{from_id}] ──[{rel}]──▶ [{to_id}]"


@mcp.tool()
def run_cypher(query: str) -> str:
    """
    Execute a raw Cypher query against the knowledge graph. Use for advanced
    analysis not covered by other tools. Read-only queries recommended.

    Args:
        query: A valid Cypher query string
    """
    try:
        rows = g.run(query)
        if not rows:
            return "Query returned no results."
        return _fmt(rows[:50])
    except Exception as e:
        return f"Cypher error: {e}"


if __name__ == "__main__":
    mcp.run()
