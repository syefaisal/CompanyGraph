import os
from typing import Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USER", "neo4j"),
                os.getenv("NEO4J_PASSWORD", "companygraph123"),
            ),
        )
    return _driver


def run(cypher: str, params: dict = None) -> list[dict]:
    with get_driver().session() as session:
        return [dict(r) for r in session.run(cypher, params or {})]


def node_dict(node) -> dict:
    d = dict(node.items())
    d["id"] = d.get("id", str(node.element_id))
    d["_labels"] = sorted(node.labels)
    d["label"] = d["_labels"][0] if d["_labels"] else "Unknown"
    return d


def get_node(node_id: str) -> Optional[dict]:
    rows = run("MATCH (n {id: $id}) RETURN n", {"id": node_id})
    return node_dict(rows[0]["n"]) if rows else None


def get_node_with_connections(node_id: str) -> Optional[dict]:
    rows = run(
        """
        MATCH (n {id: $id})
        OPTIONAL MATCH (n)-[r]-(m)
        RETURN n,
               collect({
                 rel_type: type(r),
                 direction: CASE WHEN startNode(r).id = $id THEN 'out' ELSE 'in' END,
                 neighbor_id: m.id,
                 neighbor_name: m.name,
                 neighbor_labels: labels(m)
               }) AS conns
        """,
        {"id": node_id},
    )
    if not rows:
        return None
    node = node_dict(rows[0]["n"])
    node["connections"] = [c for c in rows[0]["conns"] if c["neighbor_id"] is not None]
    return node


def get_full_graph() -> dict:
    nodes_raw = run("MATCH (n) RETURN n")
    rels_raw = run("MATCH (a)-[r]->(b) RETURN type(r) AS type, a.id AS from_id, b.id AS to_id, properties(r) AS props")
    return {
        "nodes": [node_dict(r["n"]) for r in nodes_raw],
        "relationships": [{"type": r["type"], "from_id": r["from_id"], "to_id": r["to_id"], **r["props"]} for r in rels_raw],
    }


def search_nodes(keyword: str, label: str = None) -> list[dict]:
    label_filter = f":{label}" if label else ""
    rows = run(
        f"""
        MATCH (n{label_filter})
        WHERE toLower(n.name) CONTAINS toLower($kw)
           OR toLower(coalesce(n.description, '')) CONTAINS toLower($kw)
           OR toLower(coalesce(n.role, '')) CONTAINS toLower($kw)
        RETURN n LIMIT 50
        """,
        {"kw": keyword},
    )
    return [node_dict(r["n"]) for r in rows]


def find_shortest_path(from_id: str, to_id: str) -> Optional[list[dict]]:
    rows = run(
        """
        MATCH p = shortestPath((a {id: $from_id})-[*..10]-(b {id: $to_id}))
        RETURN [node IN nodes(p) | {id: node.id, name: node.name, labels: labels(node)}] AS path,
               [rel IN relationships(p) | type(rel)] AS rels
        """,
        {"from_id": from_id, "to_id": to_id},
    )
    if not rows:
        return None
    path_nodes = rows[0]["path"]
    path_rels = rows[0]["rels"]
    steps = []
    for i, node in enumerate(path_nodes):
        steps.append({"node": node})
        if i < len(path_rels):
            steps.append({"via": path_rels[i]})
    return steps


def get_neighbors_by_label(node_id: str, neighbor_label: str) -> list[dict]:
    rows = run(
        f"""
        MATCH (n {{id: $id}})-[r]-(m:{neighbor_label})
        RETURN m, type(r) AS rel_type
        """,
        {"id": node_id},
    )
    return [{"node": node_dict(r["m"]), "rel_type": r["rel_type"]} for r in rows]


def create_node(label: str, properties: dict) -> dict:
    import uuid, datetime
    properties.setdefault("id", str(uuid.uuid4()))
    properties.setdefault("created_at", datetime.datetime.utcnow().isoformat())
    rows = run(
        f"CREATE (n:{label} $props) RETURN n",
        {"props": properties},
    )
    return node_dict(rows[0]["n"])


def create_relationship(from_id: str, to_id: str, rel_type: str, properties: dict = None) -> bool:
    rel_type = rel_type.upper().replace(" ", "_")
    result = run(
        f"""
        MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $props
        RETURN r
        """,
        {"from_id": from_id, "to_id": to_id, "props": properties or {}},
    )
    return len(result) > 0


def delete_node(node_id: str) -> bool:
    result = run(
        "MATCH (n {id: $id}) DETACH DELETE n RETURN count(n) AS deleted",
        {"id": node_id},
    )
    return result[0]["deleted"] > 0


def list_nodes(label: str = None, limit: int = 100) -> list[dict]:
    label_filter = f":{label}" if label else ""
    rows = run(f"MATCH (n{label_filter}) RETURN n ORDER BY n.name LIMIT $limit", {"limit": limit})
    return [node_dict(r["n"]) for r in rows]


def _tokenize(text: str) -> list[str]:
    import re
    return re.findall(r"\w+", text.lower())


def _node_to_text(node: dict) -> str:
    fields = ["name", "description", "role", "category", "title", "rationale", "industry", "type"]
    return " ".join(str(node.get(f, "")) for f in fields if node.get(f))


def _bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    df: dict[str, int],
    N: int,
    avgdl: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    import math
    freq: dict[str, int] = {}
    for t in doc_tokens:
        freq[t] = freq.get(t, 0) + 1
    dl = len(doc_tokens)
    score = 0.0
    for term in query_tokens:
        if term not in freq:
            continue
        tf = freq[term]
        n_docs = df.get(term, 0)
        idf = math.log((N - n_docs + 0.5) / (n_docs + 0.5) + 1)
        tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(avgdl, 1)))
        score += idf * tf_norm
    return score


def hybrid_search_nodes(keyword: str, label: str = None, top_k: int = 20) -> list[dict]:
    """BM25 lexical search over all node text fields. Falls back to substring search on zero results."""
    label_filter = f":{label}" if label else ""
    rows = run(f"MATCH (n{label_filter}) RETURN n LIMIT 500")
    if not rows:
        return []

    nodes = [node_dict(r["n"]) for r in rows]
    corpus = [_tokenize(_node_to_text(n)) for n in nodes]
    query_tokens = _tokenize(keyword)

    if not query_tokens:
        return nodes[:top_k]

    N = len(corpus)
    avgdl = sum(len(d) for d in corpus) / N

    df: dict[str, int] = {}
    for doc in corpus:
        for term in set(doc):
            df[term] = df.get(term, 0) + 1

    scored = [
        (_bm25_score(query_tokens, corpus[i], df, N, avgdl), nodes[i])
        for i in range(N)
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    results = [node for score, node in scored if score > 0][:top_k]

    return results if results else search_nodes(keyword, label)


def graph_stats() -> dict:
    counts = run(
        """
        MATCH (n)
        RETURN labels(n)[0] AS label, count(*) AS count
        ORDER BY label
        """
    )
    rel_counts = run("MATCH ()-[r]->() RETURN count(r) AS total")
    return {
        "nodes": {r["label"]: r["count"] for r in counts},
        "relationships": rel_counts[0]["total"] if rel_counts else 0,
    }
