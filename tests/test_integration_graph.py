"""
Integration tests for graph.py — require a running Neo4j instance
seeded with the Meridian Property Group dataset.

Skip if Neo4j is unavailable:
    pytest -m "not integration"
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))


def _neo4j_up() -> bool:
    try:
        import graph as g
        g.graph_stats()
        return True
    except Exception:
        return False


_NEO4J_AVAILABLE = _neo4j_up()

import graph as g

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _NEO4J_AVAILABLE, reason="Neo4j not reachable"),
]


# ── graph_stats ───────────────────────────────────────────────────────────────

class TestGraphStats:
    def test_returns_dict_with_nodes_and_relationships(self):
        stats = g.graph_stats()
        assert "nodes" in stats
        assert "relationships" in stats

    def test_meridian_person_count(self):
        assert g.graph_stats()["nodes"]["Person"] == 8

    def test_meridian_product_count(self):
        assert g.graph_stats()["nodes"]["Product"] == 5

    def test_meridian_customer_count(self):
        assert g.graph_stats()["nodes"]["Customer"] == 5

    def test_meridian_workflow_count(self):
        assert g.graph_stats()["nodes"]["Workflow"] == 6

    def test_meridian_decision_count(self):
        assert g.graph_stats()["nodes"]["Decision"] == 6

    def test_relationship_count_at_least_60(self):
        assert g.graph_stats()["relationships"] >= 60


# ── list_nodes ────────────────────────────────────────────────────────────────

class TestListNodes:
    def test_list_all_returns_30_nodes(self):
        nodes = g.list_nodes()
        assert len(nodes) == 30

    def test_list_persons_returns_8(self):
        nodes = g.list_nodes(label="Person")
        assert len(nodes) == 8

    def test_list_products_contains_leasetrack(self):
        nodes = g.list_nodes(label="Product")
        names = [n["name"] for n in nodes]
        assert "LeaseTrack" in names

    def test_list_products_contains_deprecated(self):
        nodes = g.list_nodes(label="Product")
        names = [n["name"] for n in nodes]
        assert "LegacyPortal" in names  # deprecated still in graph

    def test_list_workflows_returns_6(self):
        nodes = g.list_nodes(label="Workflow")
        assert len(nodes) == 6

    def test_list_decisions_contains_gdpr(self):
        nodes = g.list_nodes(label="Decision")
        names = [n["name"] for n in nodes]
        assert any("GDPR" in n for n in names)

    def test_limit_respected(self):
        nodes = g.list_nodes(limit=3)
        assert len(nodes) <= 3

    def test_node_has_required_fields(self):
        nodes = g.list_nodes(label="Person", limit=1)
        assert len(nodes) == 1
        node = nodes[0]
        assert "id" in node
        assert "name" in node
        assert "label" in node


# ── get_node ──────────────────────────────────────────────────────────────────

class TestGetNode:
    def test_get_david_chen(self):
        node = g.get_node("p6")
        assert node is not None
        assert node["name"] == "David Chen"
        assert node["label"] == "Person"

    def test_get_leasetrack(self):
        node = g.get_node("pr1")
        assert node is not None
        assert node["name"] == "LeaseTrack"

    def test_get_fair_housing_audit(self):
        node = g.get_node("w4")
        assert node is not None
        assert node["name"] == "Fair Housing Audit"

    def test_get_gdpr_decision(self):
        node = g.get_node("d4")
        assert node is not None
        assert "GDPR" in node["name"]

    def test_get_nonexistent_returns_none(self):
        assert g.get_node("nonexistent_xyz_abc") is None

    def test_node_has_id_and_label(self):
        node = g.get_node("c1")
        assert node["id"] == "c1"
        assert node["label"] == "Customer"


# ── get_node_with_connections ─────────────────────────────────────────────────

class TestGetNodeWithConnections:
    def test_returns_connections_key(self):
        node = g.get_node_with_connections("w4")
        assert "connections" in node

    def test_fair_housing_audit_owned_by_david_chen(self):
        node = g.get_node_with_connections("w4")
        names = [c["neighbor_name"] for c in node["connections"]]
        assert "David Chen" in names

    def test_lease_renewal_depends_on_fair_housing(self):
        node = g.get_node_with_connections("w1")
        rel_types = [c["rel_type"] for c in node["connections"]]
        assert "DEPENDS_ON" in rel_types

    def test_connection_has_all_required_fields(self):
        node = g.get_node_with_connections("p1")
        assert len(node["connections"]) > 0
        conn = node["connections"][0]
        for field in ("rel_type", "direction", "neighbor_id", "neighbor_name", "neighbor_labels"):
            assert field in conn, f"Missing field: {field}"

    def test_direction_values_are_valid(self):
        node = g.get_node_with_connections("p4")
        for conn in node["connections"]:
            assert conn["direction"] in ("in", "out")

    def test_nonexistent_node_returns_none(self):
        assert g.get_node_with_connections("nonexistent_xyz") is None

    def test_sunstone_uses_leasetrack(self):
        node = g.get_node_with_connections("c1")
        out_neighbors = [
            c["neighbor_name"] for c in node["connections"] if c["direction"] == "out"
        ]
        assert "LeaseTrack" in out_neighbors


# ── get_full_graph ────────────────────────────────────────────────────────────

class TestGetFullGraph:
    def test_returns_nodes_and_relationships(self):
        graph = g.get_full_graph()
        assert "nodes" in graph
        assert "relationships" in graph

    def test_node_count(self):
        graph = g.get_full_graph()
        assert len(graph["nodes"]) == 30

    def test_relationship_count(self):
        graph = g.get_full_graph()
        assert len(graph["relationships"]) >= 60

    def test_relationship_has_type_from_to(self):
        graph = g.get_full_graph()
        rel = graph["relationships"][0]
        assert "type" in rel
        assert "from_id" in rel
        assert "to_id" in rel


# ── search_nodes ──────────────────────────────────────────────────────────────

class TestSearchNodes:
    def test_finds_rachel_torres_by_name(self):
        results = g.search_nodes("Rachel Torres")
        assert any(r["name"] == "Rachel Torres" for r in results)

    def test_case_insensitive(self):
        results = g.search_nodes("rachel torres")
        assert any(r["name"] == "Rachel Torres" for r in results)

    def test_label_filter_restricts_type(self):
        results = g.search_nodes("lease", label="Workflow")
        assert all(r["label"] == "Workflow" for r in results)

    def test_finds_by_description(self):
        # Fair Housing Audit description contains "federal"
        results = g.search_nodes("federal")
        assert any("Fair Housing" in r["name"] for r in results)

    def test_no_match_returns_empty_list(self):
        results = g.search_nodes("zzznosuchthing999xyz")
        assert results == []


# ── hybrid_search_nodes ───────────────────────────────────────────────────────

class TestHybridSearchNodes:
    def test_compliance_query_returns_relevant_results(self):
        results = g.hybrid_search_nodes("compliance")
        names = [r["name"] for r in results]
        assert any("Compliance" in n or "Chen" in n or "Fair Housing" in n for n in names)

    def test_bm25_ranks_exact_match_in_top_3(self):
        results = g.hybrid_search_nodes("fair housing audit")
        top_names = [r["name"] for r in results[:3]]
        assert any("Fair Housing" in n for n in top_names)

    def test_label_filter_respected(self):
        results = g.hybrid_search_nodes("lease", label="Workflow")
        assert all(r["label"] == "Workflow" for r in results)

    def test_returns_list(self):
        results = g.hybrid_search_nodes("maintenance")
        assert isinstance(results, list)

    def test_fallback_on_no_bm25_match(self):
        # Proper noun unlikely to score via BM25 tokens; falls back to substring
        results = g.hybrid_search_nodes("Sofia Nguyen")
        assert any(r["name"] == "Sofia Nguyen" for r in results)

    def test_vendor_network_query(self):
        results = g.hybrid_search_nodes("vendor network outsource")
        names = [r["name"] for r in results]
        assert any("Vendor" in n or "Outsource" in n for n in names)


# ── find_shortest_path ────────────────────────────────────────────────────────

class TestFindShortestPath:
    def test_direct_owner_path(self):
        # Rachel Torres (p7) -[OWNS]-> Lease Renewal (w1)
        path = g.find_shortest_path("p7", "w1")
        assert path is not None
        assert len(path) >= 3  # source node + edge + target node

    def test_path_has_node_and_via_steps(self):
        path = g.find_shortest_path("p7", "w1")
        node_steps = [s for s in path if "node" in s]
        edge_steps = [s for s in path if "via" in s]
        assert len(node_steps) >= 2
        assert len(edge_steps) >= 1

    def test_multi_hop_path_elena_to_apex(self):
        # Elena (p1) -[MADE]-> Enter Commercial Market (d2) -[AFFECTS]-> Apex Commercial (c5)
        path = g.find_shortest_path("p1", "c5")
        assert path is not None
        assert len(path) >= 5  # at least 3 nodes + 2 edges

    def test_no_path_returns_none(self):
        path = g.find_shortest_path("nonexistent_a", "nonexistent_b")
        assert path is None

    def test_compliance_officer_path_to_audit_workflow(self):
        # David Chen (p6) -[OWNS]-> Fair Housing Audit (w4) — direct
        path = g.find_shortest_path("p6", "w4")
        assert path is not None
        assert len(path) >= 3


# ── create_node / delete_node ─────────────────────────────────────────────────

class TestNodeCRUD:
    def test_create_person_node(self):
        node = g.create_node("Person", {"name": "Test QA Engineer", "role": "QA"})
        try:
            assert node["name"] == "Test QA Engineer"
            assert "id" in node
            assert node["label"] == "Person"
            # Verify exists in DB
            found = g.get_node(node["id"])
            assert found is not None
            assert found["name"] == "Test QA Engineer"
        finally:
            g.delete_node(node["id"])

    def test_create_assigns_id_if_not_provided(self):
        node = g.create_node("Product", {"name": "Test Product"})
        try:
            assert node["id"] is not None
            assert len(node["id"]) > 0
        finally:
            g.delete_node(node["id"])

    def test_delete_existing_node_returns_true(self):
        node = g.create_node("Person", {"name": "Temp Delete Test"})
        result = g.delete_node(node["id"])
        assert result is True

    def test_delete_nonexistent_returns_false(self):
        result = g.delete_node("nonexistent_id_xyz_123")
        assert result is False

    def test_deleted_node_not_retrievable(self):
        node = g.create_node("Person", {"name": "Temp Gone"})
        node_id = node["id"]
        g.delete_node(node_id)
        assert g.get_node(node_id) is None


# ── create_relationship ───────────────────────────────────────────────────────

class TestCreateRelationship:
    def test_create_works_on_relationship(self):
        n1 = g.create_node("Person", {"name": "Rel Test Person"})
        n2 = g.create_node("Product", {"name": "Rel Test Product"})
        try:
            ok = g.create_relationship(n1["id"], n2["id"], "WORKS_ON")
            assert ok is True
            # Verify connection via node detail
            node = g.get_node_with_connections(n1["id"])
            neighbor_ids = [c["neighbor_id"] for c in node["connections"]]
            assert n2["id"] in neighbor_ids
        finally:
            g.delete_node(n1["id"])
            g.delete_node(n2["id"])

    def test_create_relationship_invalid_ids_returns_false(self):
        ok = g.create_relationship("bad_id_1", "bad_id_2", "WORKS_ON")
        assert ok is False

    def test_relationship_type_normalised_to_upper(self):
        n1 = g.create_node("Person", {"name": "Rel Norm A"})
        n2 = g.create_node("Product", {"name": "Rel Norm B"})
        try:
            # lowercase input should be normalised
            ok = g.create_relationship(n1["id"], n2["id"], "works_on")
            assert ok is True
        finally:
            g.delete_node(n1["id"])
            g.delete_node(n2["id"])


# ── Seed data integrity ───────────────────────────────────────────────────────

class TestSeedDataIntegrity:
    """Verify the Meridian Property Group dataset is correctly loaded."""

    def test_rachel_torres_owns_lease_renewal(self):
        node = g.get_node_with_connections("p7")
        outbound = [c for c in node["connections"] if c["direction"] == "out" and c["rel_type"] == "OWNS"]
        owned_names = [c["neighbor_name"] for c in outbound]
        assert "Lease Renewal" in owned_names

    def test_david_chen_owns_fair_housing_audit(self):
        node = g.get_node_with_connections("p6")
        outbound = [c for c in node["connections"] if c["direction"] == "out" and c["rel_type"] == "OWNS"]
        owned_names = [c["neighbor_name"] for c in outbound]
        assert "Fair Housing Audit" in owned_names

    def test_sunstone_uses_three_products(self):
        node = g.get_node_with_connections("c1")
        uses = [c for c in node["connections"] if c["rel_type"] == "USES"]
        assert len(uses) >= 3

    def test_lease_renewal_depends_on_fair_housing_audit(self):
        node = g.get_node_with_connections("w1")
        deps = [c for c in node["connections"]
                if c["rel_type"] == "DEPENDS_ON" and c["direction"] == "out"]
        names = [c["neighbor_name"] for c in deps]
        assert "Fair Housing Audit" in names

    def test_gdpr_decision_affects_leasetrack_and_tenantpay(self):
        node = g.get_node_with_connections("d4")
        affected = [c["neighbor_name"] for c in node["connections"]
                    if c["rel_type"] == "AFFECTS" and c["direction"] == "out"]
        assert "LeaseTrack" in affected
        assert "TenantPay" in affected

    def test_marcus_webb_works_on_leasetrack_and_maintenanceos(self):
        node = g.get_node_with_connections("p4")
        products = [c["neighbor_name"] for c in node["connections"]
                    if c["rel_type"] == "WORKS_ON" and c["direction"] == "out"]
        assert "LeaseTrack" in products
        assert "MaintenanceOS" in products

    def test_elena_made_enter_commercial_market(self):
        node = g.get_node_with_connections("p1")
        decisions = [c["neighbor_name"] for c in node["connections"]
                     if c["rel_type"] == "MADE" and c["direction"] == "out"]
        assert any("Commercial" in d for d in decisions)

    def test_legacyportal_is_deprecated(self):
        node = g.get_node("pr5")
        assert node["status"] == "deprecated"

    def test_ownerinsight_is_beta(self):
        node = g.get_node("pr4")
        assert node["status"] == "beta"

    def test_apex_commercial_is_enterprise(self):
        node = g.get_node("c5")
        assert node["tier"] == "enterprise"
