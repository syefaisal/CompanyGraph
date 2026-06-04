"""
Unit tests for the document → graph extraction contract in doc_to_graph.py.

No external services — these validate the static EXTRACTION_TOOL schema Claude
must fill, and (critically) that its label / relationship-type enums stay in
sync with the rest of the system. Schema drift between the extractor and the
graph layer is the real bug risk this file guards against.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from doc_to_graph import EXTRACTION_TOOL, SYSTEM_PROMPT
import mcp_server  # authoritative VALID_LABELS / VALID_REL_TYPES (no DB/LLM at import)

# Canonical graph vocabulary — mirrored here so a change to either side trips a test.
GRAPH_LABELS = {"Person", "Product", "Customer", "Workflow", "Decision"}
REL_TYPES = {
    "WORKS_ON", "OWNS", "MADE", "INVOLVES",
    "USES", "AFFECTS", "DEPENDS_ON", "PRODUCES",
}


def _schema() -> dict:
    return EXTRACTION_TOOL["input_schema"]


def _label_enum() -> list:
    return _schema()["properties"]["entities"]["items"]["properties"]["label"]["enum"]


def _reltype_enum() -> list:
    return _schema()["properties"]["relationships"]["items"]["properties"]["rel_type"]["enum"]


# ── Tool shape ────────────────────────────────────────────────────────────────

class TestExtractionToolShape:
    def test_tool_name_is_save_knowledge_graph(self):
        assert EXTRACTION_TOOL["name"] == "save_knowledge_graph"

    def test_has_description_and_object_schema(self):
        assert EXTRACTION_TOOL.get("description")
        assert _schema()["type"] == "object"

    def test_requires_entities_and_relationships(self):
        assert set(_schema()["required"]) == {"entities", "relationships"}

    def test_entities_and_relationships_are_arrays(self):
        props = _schema()["properties"]
        assert props["entities"]["type"] == "array"
        assert props["relationships"]["type"] == "array"

    def test_entity_items_require_id_label_name(self):
        req = set(_schema()["properties"]["entities"]["items"]["required"])
        assert req == {"id", "label", "name"}

    def test_relationship_items_require_from_rel_to(self):
        req = set(_schema()["properties"]["relationships"]["items"]["required"])
        assert req == {"from_id", "rel_type", "to_id"}

    def test_system_prompt_forces_single_call(self):
        # The prompt must instruct exactly one save_knowledge_graph call.
        assert "save_knowledge_graph" in SYSTEM_PROMPT
        assert "exactly once" in SYSTEM_PROMPT.lower()


# ── Schema stays in sync with the rest of the system ──────────────────────────

class TestSchemaInSyncWithGraph:
    def test_label_enum_matches_graph_labels(self):
        assert set(_label_enum()) == GRAPH_LABELS

    def test_reltype_enum_matches_relationship_types(self):
        assert set(_reltype_enum()) == REL_TYPES

    def test_no_duplicate_labels(self):
        labels = _label_enum()
        assert len(labels) == len(set(labels))

    def test_no_duplicate_rel_types(self):
        rels = _reltype_enum()
        assert len(rels) == len(set(rels))

    def test_labels_match_mcp_server(self):
        assert set(_label_enum()) == mcp_server.VALID_LABELS

    def test_rel_types_match_mcp_server(self):
        assert set(_reltype_enum()) == mcp_server.VALID_REL_TYPES
