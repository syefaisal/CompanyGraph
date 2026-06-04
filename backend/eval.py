"""
Offline evaluation harness for the Meridian Property Group knowledge graph API.

Runs 8 PropTech test cases against POST /query and scores each response for:
  - entity_recall   fraction of expected entities mentioned in the answer
  - latency_ms      wall-clock time from request start to full response
  - model           which model was routed to (direct / haiku / sonnet)
  - pass            entity_recall >= 0.6

Results are saved to:
  - eval_results/YYYY-MM-DD_HH-MM_<mode>.json   always (local disk)
  - LangSmith dataset "cogni-graph-eval"          when LANGSMITH_API_KEY is set

Usage:
    python eval.py                         # runs against localhost:8000
    python eval.py --url http://host:8000  # custom API URL
    python eval.py --agent                 # use /query/agent instead of /query
    python eval.py --verbose               # print full answer text per case
    python eval.py --out results.json      # override output file path
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

# eval.py runs as its own process (HTTP client to the API), so it must load
# .env itself — unlike graph.py/api.py, nothing else loads it here. Point at
# the repo-root .env explicitly so it works from any working directory.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ── Test suite ────────────────────────────────────────────────────────────────

TEST_CASES = [
    {
        "id": "tc_01",
        "category": "workflow_ownership",
        "question": "Who owns the Lease Renewal workflow and who else is involved?",
        "expected_entities": ["Rachel Torres", "Lease Renewal", "Priya Okafor", "Andre Williams"],
    },
    {
        "id": "tc_02",
        "category": "compliance",
        "question": "What compliance-related decisions has Meridian made, and who drove them?",
        "expected_entities": ["GDPR", "CCPA", "David Chen", "Fair Housing"],
    },
    {
        "id": "tc_03",
        "category": "customer_products",
        "question": "Which customers use MaintenanceOS?",
        "expected_entities": ["MaintenanceOS", "Sunstone Residential", "Metro Living Group", "Apex Commercial"],
    },
    {
        "id": "tc_04",
        "category": "decision_impact",
        "question": "Trace the full impact of the decision to deprecate LegacyPortal.",
        "expected_entities": ["LegacyPortal", "Deprecate", "James Park"],
    },
    {
        "id": "tc_05",
        "category": "path_finding",
        "question": "How is Elena Rodriguez connected to Apex Commercial?",
        "expected_entities": ["Elena Rodriguez", "Apex Commercial"],
    },
    {
        "id": "tc_06",
        "category": "risk_analysis",
        "question": "Which workflows would be at risk if Marcus Webb left the company?",
        "expected_entities": ["Marcus Webb", "Work Order Processing"],
    },
    {
        "id": "tc_07",
        "category": "customer_360",
        "question": "What products does Sunstone Residential use and who built them?",
        "expected_entities": ["Sunstone Residential", "LeaseTrack", "MaintenanceOS", "TenantPay", "Marcus Webb"],
    },
    {
        "id": "tc_08",
        "category": "hybrid_search",
        "question": "Which engineer is responsible for payment processing at Meridian?",
        "expected_entities": ["TenantPay", "Priya Okafor"],
    },
]

PASS_THRESHOLD = 0.6
LANGSMITH_DATASET = "cogni-graph-eval"


# ── SSE reader ────────────────────────────────────────────────────────────────

def collect_sse(url: str, question: str, timeout: float = 90.0) -> tuple[str, str, float]:
    """POST to /query, consume SSE stream, return (full_text, model, latency_ms)."""
    t_start = time.time()
    full_text = ""
    model = "unknown"

    with httpx.Client(timeout=timeout) as client:
        with client.stream("POST", url, json={"question": question}) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line.startswith("data: "):
                    continue
                try:
                    event = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "text":
                    full_text += event.get("content", "")
                elif event.get("type") == "done":
                    model = event.get("model", "unknown")

    latency_ms = (time.time() - t_start) * 1000
    return full_text, model, latency_ms


# ── Scoring ───────────────────────────────────────────────────────────────────

def entity_recall(answer: str, expected: list[str]) -> float:
    """Fraction of expected entity names found (case-insensitive) in the answer."""
    if not expected:
        return 1.0
    answer_lower = answer.lower()
    hits = sum(1 for e in expected if e.lower() in answer_lower)
    return hits / len(expected)


# ── Persistence: local JSON ───────────────────────────────────────────────────

def save_json(results: list[dict], summary: dict, run_meta: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"meta": run_meta, "summary": summary, "results": results}
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"\n  Saved  → {out_path}")


# ── Persistence: LangSmith dataset ───────────────────────────────────────────

def push_to_langsmith(results: list[dict], run_meta: dict, answer_map: dict[str, str]) -> None:
    """
    Upserts each test case as an example in the LangSmith dataset
    'cogni-graph-eval', then logs the scored outputs as a run against it.
    """
    try:
        from langsmith import Client
    except ImportError:
        print("  LangSmith  skipped (langsmith not installed)")
        return

    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("  LangSmith  skipped (LANGSMITH_API_KEY not set)")
        return

    try:
        ls = Client(api_key=api_key)
        project = os.getenv("LANGSMITH_PROJECT", "cogni-graph")

        # Get or create the eval dataset
        try:
            dataset = ls.read_dataset(dataset_name=LANGSMITH_DATASET)
        except Exception:
            dataset = ls.create_dataset(
                dataset_name=LANGSMITH_DATASET,
                description="PropTech knowledge graph eval — Meridian Property Group",
            )

        # Upsert examples (one per test case)
        existing = {ex.metadata.get("tc_id"): ex for ex in ls.list_examples(dataset_id=dataset.id)
                    if ex.metadata.get("tc_id")}

        for tc in TEST_CASES:
            tc_id = tc["id"]
            inputs = {"question": tc["question"]}
            outputs = {"expected_entities": tc["expected_entities"]}
            meta = {"tc_id": tc_id, "category": tc["category"]}

            if tc_id in existing:
                ls.update_example(existing[tc_id].id, inputs=inputs, outputs=outputs, metadata=meta)
            else:
                ls.create_example(inputs=inputs, outputs=outputs, dataset_id=dataset.id, metadata=meta)

        # Log this eval run's scored outputs
        run_name = f"eval-{run_meta['timestamp']}-{run_meta['mode']}"
        for r in results:
            tc = next(t for t in TEST_CASES if t["id"] == r["id"])
            ls.create_run(
                name=run_name,
                run_type="chain",
                project_name=project,
                inputs={"question": tc["question"]},
                outputs={
                    "answer": answer_map.get(r["id"], ""),
                    "entity_recall": r["recall"],
                    "passed": r["passed"],
                    "model": r["model"],
                    "latency_ms": r["latency_ms"],
                },
                extra={
                    "metadata": {
                        "tc_id": r["id"],
                        "category": r["category"],
                        "mode": run_meta["mode"],
                        "eval_run": run_meta["timestamp"],
                    }
                },
            )

        print(f"  LangSmith → dataset '{LANGSMITH_DATASET}' updated, {len(results)} runs logged to '{project}'")

    except Exception as exc:
        print(f"  LangSmith  error: {exc}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Eval harness for knowledge graph API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--agent", action="store_true", help="Use /query/agent endpoint")
    parser.add_argument("--verbose", action="store_true", help="Print full answer for each case")
    parser.add_argument("--out", default=None, help="Override output JSON file path")
    args = parser.parse_args()

    endpoint = f"{args.url}/query/agent" if args.agent else f"{args.url}/query"
    mode_label = "agent" if args.agent else "standard"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")

    print(f"\n{'='*72}")
    print(f"  Meridian Property Group — Knowledge Graph Eval ({mode_label} mode)")
    print(f"  Endpoint : {endpoint}")
    print(f"  Cases    : {len(TEST_CASES)}")
    print(f"{'='*72}\n")

    results = []
    answer_map: dict[str, str] = {}   # tc_id → full answer text (for LangSmith)

    for tc in TEST_CASES:
        print(f"  [{tc['id']}] {tc['category']:<22} ", end="", flush=True)
        try:
            answer, model, latency_ms = collect_sse(endpoint, tc["question"])
            recall = entity_recall(answer, tc["expected_entities"])
            passed = recall >= PASS_THRESHOLD
            status = "PASS" if passed else "FAIL"
            print(f"{status}  recall={recall:.2f}  {round(latency_ms):>5} ms  [{model}]")
            if args.verbose:
                print(f"\n  Q: {tc['question']}")
                print(f"  A: {answer[:300]}{'...' if len(answer) > 300 else ''}\n")
            answer_map[tc["id"]] = answer
            results.append({
                "id": tc["id"],
                "category": tc["category"],
                "passed": passed,
                "recall": recall,
                "latency_ms": round(latency_ms),
                "model": model,
            })
        except Exception as exc:
            print(f"ERROR: {exc}")
            answer_map[tc["id"]] = ""
            results.append({
                "id": tc["id"],
                "category": tc["category"],
                "passed": False,
                "recall": 0.0,
                "latency_ms": 0,
                "model": "error",
                "error": str(exc),
            })

    # ── Summary ───────────────────────────────────────────────────────────────
    passed_list = [r for r in results if r["passed"]]
    avg_recall = sum(r["recall"] for r in results) / len(results)
    avg_latency = sum(r["latency_ms"] for r in results if r["latency_ms"] > 0) / max(
        len([r for r in results if r["latency_ms"] > 0]), 1
    )
    model_dist: dict[str, int] = {}
    for r in results:
        model_dist[r["model"]] = model_dist.get(r["model"], 0) + 1

    print(f"\n{'─'*72}")
    print(f"  Pass rate   : {len(passed_list)}/{len(results)} ({100*len(passed_list)//len(results)}%)")
    print(f"  Avg recall  : {avg_recall:.2f}")
    print(f"  Avg latency : {round(avg_latency)} ms")
    print(f"  Model dist  : {model_dist}")
    print(f"{'='*72}\n")

    # ── Category breakdown ────────────────────────────────────────────────────
    categories: dict[str, list] = {}
    for r in results:
        categories.setdefault(r["category"], []).append(r)
    print("  Category breakdown:")
    for cat, items in sorted(categories.items()):
        cat_pass = sum(1 for r in items if r["passed"])
        cat_recall = sum(r["recall"] for r in items) / len(items)
        print(f"    {cat:<24} {cat_pass}/{len(items)}  recall={cat_recall:.2f}")
    print()

    # ── Persist results ───────────────────────────────────────────────────────
    summary = {
        "pass_rate": f"{len(passed_list)}/{len(results)}",
        "avg_recall": round(avg_recall, 3),
        "avg_latency_ms": round(avg_latency),
        "model_distribution": model_dist,
    }
    run_meta = {
        "timestamp": timestamp,
        "mode": mode_label,
        "endpoint": endpoint,
        "pass_threshold": PASS_THRESHOLD,
    }

    # 1. Local JSON
    out_path = Path(args.out) if args.out else Path("eval_results") / f"{timestamp}_{mode_label}.json"
    save_json(results, summary, run_meta, out_path)

    # 2. LangSmith dataset (no-op if key is absent)
    push_to_langsmith(results, run_meta, answer_map)


if __name__ == "__main__":
    main()
