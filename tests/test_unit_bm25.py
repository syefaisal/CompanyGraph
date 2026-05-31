"""
Unit tests for the BM25 hybrid search implementation in graph.py.
No external services required — pure algorithm correctness.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from graph import _tokenize, _bm25_score, _node_to_text


# ── _tokenize ─────────────────────────────────────────────────────────────────

class TestTokenize:
    def test_lowercases_input(self):
        assert _tokenize("Lease RENEWAL Workflow") == ["lease", "renewal", "workflow"]

    def test_splits_on_non_word_chars(self):
        toks = _tokenize("work-order compliance/audit")
        assert "work" in toks
        assert "order" in toks
        assert "compliance" in toks
        assert "audit" in toks

    def test_empty_string_returns_empty_list(self):
        assert _tokenize("") == []

    def test_numbers_are_tokens(self):
        toks = _tokenize("v3.1 mrr 95000")
        assert "95000" in toks

    def test_preserves_multiple_word_tokens(self):
        toks = _tokenize("fair housing audit quarterly")
        assert toks == ["fair", "housing", "audit", "quarterly"]

    def test_strips_punctuation(self):
        toks = _tokenize("GDPR, CCPA — compliance!")
        assert "gdpr" in toks
        assert "ccpa" in toks
        assert "compliance" in toks
        assert "," not in toks
        assert "!" not in toks

    def test_single_word(self):
        assert _tokenize("LeaseTrack") == ["leasetrack"]


# ── _bm25_score ───────────────────────────────────────────────────────────────

class TestBm25Score:
    """BM25 correctness: IDF weighting, term frequency, document-length normalisation."""

    def _make_df(self, corpus: list[list[str]]) -> dict[str, int]:
        df: dict[str, int] = {}
        for doc in corpus:
            for term in set(doc):
                df[term] = df.get(term, 0) + 1
        return df

    def test_matching_term_scores_positive(self):
        corpus = [["lease", "renewal"], ["work", "order"]]
        df = self._make_df(corpus)
        avgdl = sum(len(d) for d in corpus) / len(corpus)
        score = _bm25_score(["lease"], corpus[0], df, N=2, avgdl=avgdl)
        assert score > 0

    def test_non_matching_term_scores_zero(self):
        corpus = [["lease", "renewal"], ["work", "order"]]
        df = self._make_df(corpus)
        avgdl = 2.0
        score = _bm25_score(["compliance"], corpus[0], df, N=2, avgdl=avgdl)
        assert score == 0.0

    def test_more_query_hits_score_higher(self):
        corpus = [
            ["compliance", "audit", "housing"],
            ["compliance", "vendor", "onboarding"],
        ]
        df = self._make_df(corpus)
        avgdl = 3.0
        score_both = _bm25_score(["compliance", "audit"], corpus[0], df, N=2, avgdl=avgdl)
        score_one = _bm25_score(["compliance", "audit"], corpus[1], df, N=2, avgdl=avgdl)
        assert score_both > score_one

    def test_rare_term_scores_higher_than_common(self):
        # "rare" appears in 1/10 docs; "common" in 9/10
        N = 10
        df = {"rare": 1, "common": 9}
        avgdl = 3.0
        doc = ["rare", "common", "word"]
        score_rare = _bm25_score(["rare"], doc, df, N=N, avgdl=avgdl)
        score_common = _bm25_score(["common"], doc, df, N=N, avgdl=avgdl)
        assert score_rare > score_common

    def test_empty_query_tokens_scores_zero(self):
        df = {"lease": 1}
        score = _bm25_score([], ["lease", "renewal"], df, N=5, avgdl=2.0)
        assert score == 0.0

    def test_empty_document_scores_zero(self):
        df = {"lease": 1}
        score = _bm25_score(["lease"], [], df, N=5, avgdl=2.0)
        assert score == 0.0

    def test_repeated_term_in_doc_scores_higher(self):
        # Document with "audit audit audit" should score higher than "audit" alone
        N = 5
        df = {"audit": 3}
        avgdl = 3.0
        score_many = _bm25_score(["audit"], ["audit", "audit", "audit"], df, N=N, avgdl=avgdl)
        score_one = _bm25_score(["audit"], ["audit", "other", "text"], df, N=N, avgdl=avgdl)
        assert score_many > score_one


# ── _node_to_text ─────────────────────────────────────────────────────────────

class TestNodeToText:
    def test_extracts_name(self):
        node = {"name": "David Chen", "id": "p6", "_labels": ["Person"]}
        text = _node_to_text(node)
        assert "David Chen" in text

    def test_extracts_description(self):
        node = {"name": "Fair Housing Audit", "description": "federal compliance regulations", "id": "w4"}
        text = _node_to_text(node)
        assert "federal compliance regulations" in text

    def test_extracts_role(self):
        node = {"name": "David Chen", "role": "Director of Compliance"}
        text = _node_to_text(node)
        assert "Director of Compliance" in text

    def test_extracts_rationale(self):
        node = {"name": "GDPR Overhaul", "rationale": "proactive compliance ahead of regulation"}
        text = _node_to_text(node)
        assert "proactive compliance" in text

    def test_skips_missing_fields(self):
        node = {"name": "LeaseTrack"}
        text = _node_to_text(node)
        assert "LeaseTrack" in text
        assert "None" not in text

    def test_concatenates_all_relevant_fields(self):
        node = {
            "name": "MaintenanceOS",
            "category": "Work Order Management",
            "description": "vendor coordination platform",
            "id": "pr2",
        }
        text = _node_to_text(node)
        assert "MaintenanceOS" in text
        assert "Work Order Management" in text
        assert "vendor coordination" in text

    def test_ignores_id_and_label(self):
        node = {"name": "LeaseTrack", "id": "pr1", "_labels": ["Product"], "label": "Product"}
        text = _node_to_text(node)
        # id and _labels are not in the fields list, so they should not appear
        assert "pr1" not in text
