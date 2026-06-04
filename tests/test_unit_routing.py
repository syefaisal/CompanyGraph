"""
Unit tests for query routing logic, direct-answer short-circuit, and cost budget
enforcement in api.py. No external services required — Neo4j calls are mocked.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from unittest.mock import patch
import api
from api import route_query, _try_direct_answer, _metrics, _DAILY_COST_LIMIT_USD


# ── route_query ───────────────────────────────────────────────────────────────

class TestRouteQuery:
    """Simple lookups → haiku; anything with complexity indicators → sonnet."""

    def test_simple_person_lookup_routes_to_haiku(self):
        assert route_query("who is Rachel Torres") == "claude-haiku-4-5-20251001"

    def test_simple_product_lookup_routes_to_haiku(self):
        assert route_query("what is TenantPay") == "claude-haiku-4-5-20251001"

    def test_keyword_workflow_routes_to_sonnet(self):
        assert route_query("what workflows does James Park own") == "claude-sonnet-4-6"

    def test_keyword_impact_routes_to_sonnet(self):
        assert route_query("what is the impact of the deprecation") == "claude-sonnet-4-6"

    def test_keyword_compliance_routes_to_sonnet(self):
        assert route_query("compliance posture across all products") == "claude-sonnet-4-6"

    def test_keyword_trace_routes_to_sonnet(self):
        assert route_query("trace the blast radius of the GDPR decision") == "claude-sonnet-4-6"

    def test_keyword_path_routes_to_sonnet(self):
        assert route_query("find the path between Elena and Apex") == "claude-sonnet-4-6"

    def test_keyword_risk_routes_to_sonnet(self):
        assert route_query("risk analysis for vendor onboarding") == "claude-sonnet-4-6"

    def test_keyword_depend_routes_to_sonnet(self):
        assert route_query("what does lease renewal depend on") == "claude-sonnet-4-6"

    def test_keyword_decision_routes_to_sonnet(self):
        assert route_query("which decision affected TenantPay") == "claude-sonnet-4-6"

    def test_long_question_routes_to_sonnet(self):
        long_q = "who is the engineer responsible for building the payment processing module at Meridian"
        assert len(long_q.split()) > 12
        assert route_query(long_q) == "claude-sonnet-4-6"

    def test_case_insensitive(self):
        # "WORKFLOW" should still match the lowercase indicator
        assert route_query("WORKFLOW dependencies") == "claude-sonnet-4-6"

    def test_returns_string(self):
        result = route_query("any question")
        assert isinstance(result, str)
        assert result in ("claude-haiku-4-5-20251001", "claude-sonnet-4-6")


# ── _try_direct_answer ────────────────────────────────────────────────────────

class TestTryDirectAnswer:
    """Direct answers bypass the LLM for simple list/count queries."""

    # -- Count queries --

    def test_how_many_workflows(self):
        with patch("api.g") as mock_g:
            mock_g.graph_stats.return_value = {
                "nodes": {"Workflow": 6, "Person": 8}, "relationships": 71
            }
            result = _try_direct_answer("how many workflows are there")
        assert result is not None
        assert "6" in result
        assert "Workflow" in result

    def test_how_many_products(self):
        with patch("api.g") as mock_g:
            mock_g.graph_stats.return_value = {
                "nodes": {"Product": 5}, "relationships": 71
            }
            result = _try_direct_answer("how many products")
        assert result is not None
        assert "5" in result

    def test_count_of_customers(self):
        with patch("api.g") as mock_g:
            mock_g.graph_stats.return_value = {"nodes": {"Customer": 5}, "relationships": 71}
            result = _try_direct_answer("count of customers")
        assert result is not None
        assert "5" in result

    def test_number_of_decisions(self):
        with patch("api.g") as mock_g:
            mock_g.graph_stats.return_value = {"nodes": {"Decision": 6}, "relationships": 71}
            result = _try_direct_answer("number of decisions")
        assert result is not None
        assert "6" in result

    # -- List queries --

    def test_list_all_workflows(self):
        mock_nodes = [
            {"name": "Lease Renewal", "id": "w1"},
            {"name": "Fair Housing Audit", "id": "w4"},
        ]
        with patch("api.g") as mock_g:
            mock_g.list_nodes.return_value = mock_nodes
            result = _try_direct_answer("list all workflows")
        assert result is not None
        assert "Lease Renewal" in result
        assert "Fair Housing Audit" in result

    def test_show_all_people(self):
        mock_nodes = [
            {"name": "Rachel Torres", "id": "p7"},
            {"name": "David Chen", "id": "p6"},
        ]
        with patch("api.g") as mock_g:
            mock_g.list_nodes.return_value = mock_nodes
            result = _try_direct_answer("show all people")
        assert result is not None
        assert "Rachel Torres" in result
        assert "David Chen" in result

    def test_list_all_products(self):
        mock_nodes = [{"name": "LeaseTrack", "id": "pr1"}, {"name": "TenantPay", "id": "pr3"}]
        with patch("api.g") as mock_g:
            mock_g.list_nodes.return_value = mock_nodes
            result = _try_direct_answer("list all products")
        assert result is not None
        assert "LeaseTrack" in result

    def test_list_all_customers(self):
        mock_nodes = [{"name": "Sunstone Residential", "id": "c1"}]
        with patch("api.g") as mock_g:
            mock_g.list_nodes.return_value = mock_nodes
            result = _try_direct_answer("list all customers")
        assert result is not None
        assert "Sunstone Residential" in result

    def test_list_calls_correct_label(self):
        """Verify list_nodes is called with the right Neo4j label."""
        with patch("api.g") as mock_g:
            mock_g.list_nodes.return_value = []
            _try_direct_answer("list all workflows")
            mock_g.list_nodes.assert_called_once_with(label="Workflow")

    def test_count_calls_graph_stats(self):
        with patch("api.g") as mock_g:
            mock_g.graph_stats.return_value = {"nodes": {"Decision": 6}, "relationships": 71}
            _try_direct_answer("how many decisions")
            mock_g.graph_stats.assert_called_once()

    # -- Non-direct queries return None --

    def test_complex_question_returns_none(self):
        result = _try_direct_answer("who owns the lease renewal workflow")
        assert result is None

    def test_arbitrary_question_returns_none(self):
        result = _try_direct_answer("trace the compliance impact of GDPR")
        assert result is None

    def test_empty_string_returns_none(self):
        result = _try_direct_answer("")
        assert result is None

    def test_partial_match_without_trigger_returns_none(self):
        # "workflows" without "list all" / "show all" / "how many" trigger
        result = _try_direct_answer("tell me about workflows")
        assert result is None


# ── Cost budget enforcement ───────────────────────────────────────────────────

class TestCostBudgetEnforcement:
    """
    Tests that route_query() forces Haiku when the daily cost budget is exceeded,
    and that _update_metrics() sets the flag when the limit is reached.
    """

    def setup_method(self):
        """Reset budget and token state before each test."""
        _metrics["budget_exceeded"] = False
        _metrics["budget_exceeded_at_usd"] = None
        _metrics["running_cost_usd"] = 0.0
        _metrics["total_input_tokens"] = 0
        _metrics["total_cached_tokens"] = 0
        _metrics["total_output_tokens"] = 0

    def teardown_method(self):
        """Restore clean state after each test."""
        _metrics["budget_exceeded"] = False
        _metrics["budget_exceeded_at_usd"] = None
        _metrics["running_cost_usd"] = 0.0
        _metrics["total_input_tokens"] = 0
        _metrics["total_cached_tokens"] = 0
        _metrics["total_output_tokens"] = 0

    # ── Budget not exceeded — normal routing ──────────────────────────────────

    def test_normal_routing_below_budget(self):
        _metrics["budget_exceeded"] = False
        assert route_query("who is Rachel Torres") == "claude-haiku-4-5-20251001"

    def test_complex_routes_to_sonnet_below_budget(self):
        _metrics["budget_exceeded"] = False
        assert route_query("trace the compliance impact of GDPR") == "claude-sonnet-4-6"

    # ── Budget exceeded — all queries forced to Haiku ─────────────────────────

    def test_budget_exceeded_forces_haiku_for_simple(self):
        _metrics["budget_exceeded"] = True
        assert route_query("who is Rachel Torres") == "claude-haiku-4-5-20251001"

    def test_budget_exceeded_forces_haiku_for_complex(self):
        """Even complex multi-hop reasoning must use Haiku when over budget."""
        _metrics["budget_exceeded"] = True
        result = route_query("trace the full compliance impact of the GDPR decision on all workflows")
        assert result == "claude-haiku-4-5-20251001"

    def test_budget_exceeded_forces_haiku_regardless_of_length(self):
        """Long questions that would normally go to Sonnet are also forced to Haiku."""
        _metrics["budget_exceeded"] = True
        long_q = " ".join(["word"] * 20)   # > 12 words → normally Sonnet
        assert route_query(long_q) == "claude-haiku-4-5-20251001"

    # ── _update_metrics sets the budget flag ──────────────────────────────────

    def test_update_metrics_sets_exceeded_flag(self):
        """Simulates enough token usage to exceed the budget limit."""
        from api import _update_metrics, _DAILY_COST_LIMIT_USD

        # Calculate tokens needed to exceed the limit.
        # Cost = (input * 3 + output * 15) / 1_000_000
        # Use output tokens only: tokens_needed = limit * 1_000_000 / 15
        tokens_to_exceed = int(_DAILY_COST_LIMIT_USD * 1_000_000 / 15) + 1

        class FakeUsage:
            input_tokens = 0
            cache_read_input_tokens = 0
            output_tokens = tokens_to_exceed

        _update_metrics("standard", 1000.0, FakeUsage(), "claude-sonnet-4-6")

        assert _metrics["budget_exceeded"] is True
        assert _metrics["budget_exceeded_at_usd"] is not None
        assert _metrics["budget_exceeded_at_usd"] > 0

    def test_update_metrics_does_not_set_flag_below_limit(self):
        """Small usage must not trigger the budget flag."""
        from api import _update_metrics

        class FakeUsage:
            input_tokens = 100
            cache_read_input_tokens = 0
            output_tokens = 50

        _update_metrics("standard", 500.0, FakeUsage(), "claude-haiku-4-5-20251001")

        assert _metrics["budget_exceeded"] is False

    def test_running_cost_updated_after_metrics(self):
        from api import _update_metrics

        class FakeUsage:
            input_tokens = 1000
            cache_read_input_tokens = 0
            output_tokens = 200

        _update_metrics("standard", 800.0, FakeUsage(), "claude-sonnet-4-6")
        assert _metrics["running_cost_usd"] > 0

    # ── Budget disabled when limit = 0 ────────────────────────────────────────

    def test_zero_limit_disables_budget_enforcement(self):
        """Setting DAILY_COST_LIMIT_USD=0 disables the budget check entirely."""
        from api import _update_metrics

        original_limit = api._DAILY_COST_LIMIT_USD
        api._DAILY_COST_LIMIT_USD = 0.0   # disable

        class FakeUsage:
            input_tokens = 0
            cache_read_input_tokens = 0
            output_tokens = 10_000_000   # enormous usage

        try:
            _update_metrics("standard", 1000.0, FakeUsage(), "claude-sonnet-4-6")
            assert _metrics["budget_exceeded"] is False
        finally:
            api._DAILY_COST_LIMIT_USD = original_limit
