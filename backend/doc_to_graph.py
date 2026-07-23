"""
Extract a knowledge graph from a plain-text company brief using Claude.

Claude reads the document and calls a structured tool to return all entities
and relationships, which are then written to Neo4j via the same graph.py layer
used by the REST API and MCP server.

Usage:
    python doc_to_graph.py                          # uses nexus_corp_brief.md
    python doc_to_graph.py --file my_brief.md       # custom document
    python doc_to_graph.py --dry-run                # print extracted JSON, skip Neo4j
    python doc_to_graph.py --clear                  # wipe graph first, then load
"""

import argparse
import json
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# extract_graph() calls Claude before graph.py (which loads .env) is imported,
# so load the repo-root .env here to pick up ANTHROPIC_API_KEY when run standalone.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ---------------------------------------------------------------------------
# Tool schema — Claude must call this exactly once with the extracted graph
# ---------------------------------------------------------------------------

EXTRACTION_TOOL = {
    "name": "save_knowledge_graph",
    "description": (
        "Called once after reading the document. Saves all extracted entities "
        "and relationships so they can be written to the knowledge graph database."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "description": "Every person, product, customer, workflow, and decision found.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Short unique slug, e.g. p1, p2, pr1, c1, w1, d1.",
                        },
                        "label": {
                            "type": "string",
                            "enum": ["Person", "Product", "Customer", "Workflow", "Decision"],
                        },
                        "name": {"type": "string"},
                        "properties": {
                            "type": "object",
                            "description": (
                                "Label-specific attributes. "
                                "Person: role, department, email, tenure_years. "
                                "Product: category, status, version, mrr_usd. "
                                "Customer: industry, tier, region, arr_usd, since. "
                                "Workflow: type, status, avg_duration_days, description. "
                                "Decision: title, date, outcome, rationale."
                            ),
                            "additionalProperties": True,
                        },
                    },
                    "required": ["id", "label", "name"],
                },
            },
            "relationships": {
                "type": "array",
                "description": "Every directed relationship between two entity IDs.",
                "items": {
                    "type": "object",
                    "properties": {
                        "from_id": {"type": "string"},
                        "rel_type": {
                            "type": "string",
                            "enum": [
                                "WORKS_ON",   # Person → Product
                                "OWNS",       # Person → Workflow
                                "MADE",       # Person → Decision
                                "INVOLVES",   # Workflow → Person
                                "USES",       # Customer → Product
                                "AFFECTS",    # Decision → Product | Customer | Workflow
                                "DEPENDS_ON", # Workflow → Workflow
                                "PRODUCES",   # Workflow → Product
                            ],
                        },
                        "to_id": {"type": "string"},
                    },
                    "required": ["from_id", "rel_type", "to_id"],
                },
            },
        },
        "required": ["entities", "relationships"],
    },
}

SYSTEM_PROMPT = """\
You are a knowledge graph extraction specialist. Read the company document provided by the user \
and extract every entity and relationship into a structured graph.

Call save_knowledge_graph exactly once with all entities and relationships you find. \
Do not omit any entity or relationship mentioned in the document.\
"""


# ---------------------------------------------------------------------------
# Extraction via Claude
# ---------------------------------------------------------------------------

def extract_graph(document_text: str, model: str = "claude-opus-4-8") -> dict:
    """Send the document to Claude and return the extracted {entities, relationships}."""
    client = anthropic.Anthropic()

    print(f"Sending document ({len(document_text):,} chars) to {model} for extraction…")

    response = client.messages.create(
        model=model,
        # The full graph (entities + relationships) for a company brief easily
        # exceeds a few thousand output tokens; too small a budget truncates the
        # tool call mid-JSON and drops 'relationships'. Keep this generous.
        max_tokens=16384,
        system=SYSTEM_PROMPT,
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "save_knowledge_graph"},
        messages=[
            {
                "role": "user",
                "content": f"Extract the knowledge graph from this company document:\n\n{document_text}",
            }
        ],
    )

    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            "Extraction was truncated (hit max_tokens) — the tool call is incomplete. "
            "Raise max_tokens in extract_graph() or split the document."
        )

    # tool_choice forces exactly one tool call — pull its input directly
    for block in response.content:
        if block.type == "tool_use" and block.name == "save_knowledge_graph":
            data = block.input
            if "entities" not in data or "relationships" not in data:
                raise RuntimeError(
                    "Extraction returned an incomplete graph "
                    f"(keys: {sorted(data)}); expected 'entities' and 'relationships'."
                )
            return data

    raise RuntimeError("Claude did not return a save_knowledge_graph tool call.")


# ---------------------------------------------------------------------------
# Neo4j loading
# ---------------------------------------------------------------------------

def load_into_neo4j(graph_data: dict, clear: bool = False) -> None:
    from graph import run

    entities = graph_data.get("entities", [])
    relationships = graph_data.get("relationships", [])

    if clear:
        print("Clearing existing graph…")
        run("MATCH (n) DETACH DELETE n")

    print(f"Writing {len(entities)} entities…")
    for e in entities:
        label = e["label"]
        node_id = e["id"]
        props = {"name": e["name"], **e.get("properties", {})}

        # Build SET clause from props dict
        set_parts = ", ".join(f"n.{k} = ${k}" for k in props)
        cypher = f"MERGE (n:{label} {{id: $id}}) SET {set_parts}"
        run(cypher, {"id": node_id, **props})

    print(f"Writing {len(relationships)} relationships…")
    for r in relationships:
        cypher = (
            f"MATCH (a {{id: $from_id}}), (b {{id: $to_id}}) "
            f"MERGE (a)-[:{r['rel_type']}]->(b)"
        )
        run(cypher, {"from_id": r["from_id"], "to_id": r["to_id"]})


    # Summary
    from graph import graph_stats
    stats = graph_stats()
    print("\nGraph loaded successfully!")
    print(f"  Nodes by type : {stats['nodes']}")
    print(f"  Relationships : {stats['relationships']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a knowledge graph from a document using Claude.")
    parser.add_argument("--file", default="nexus_corp_brief.md", help="Path to the source document")
    parser.add_argument("--dry-run", action="store_true", help="Print extracted JSON without writing to Neo4j")
    parser.add_argument("--clear", action="store_true", help="Delete all existing nodes before loading")
    parser.add_argument("--model", default="claude-opus-4-8", help="Claude model to use for extraction")
    args = parser.parse_args()

    doc_path = Path(args.file)
    if not doc_path.exists():
        print(f"Error: document not found: {doc_path}", file=sys.stderr)
        sys.exit(1)

    document_text = doc_path.read_text(encoding="utf-8")
    graph_data = extract_graph(document_text, model=args.model)

    if args.dry_run:
        print("\n── Extracted graph (dry run) ──────────────────────────────")
        print(json.dumps(graph_data, indent=2))
        print(f"\n{len(graph_data['entities'])} entities · {len(graph_data['relationships'])} relationships")
        return

    load_into_neo4j(graph_data, clear=args.clear)


if __name__ == "__main__":
    main()
