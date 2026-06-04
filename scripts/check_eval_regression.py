"""
Eval regression check for CI/CD.

Reads a timestamped eval result JSON file and fails (exit 1) if:
  - avg_recall < RECALL_THRESHOLD
  - pass_rate < PASS_RATE_THRESHOLD
  - any individual test case has recall == 0.0 (complete failure)

Usage:
    python scripts/check_eval_regression.py eval_results/nightly_standard.json
    python scripts/check_eval_regression.py          # auto-finds latest in eval_results/
"""

import json
import sys
from pathlib import Path

RECALL_THRESHOLD = 0.85     # avg recall must be >= this to pass
PASS_RATE_THRESHOLD = 0.75  # fraction of test cases that must pass (6/8 minimum)
ZERO_RECALL_ALLOWED = 0     # number of test cases allowed to score 0.0


def load_result(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def latest_result() -> Path:
    results_dir = Path("backend/eval_results") if Path("backend/eval_results").exists() else Path("eval_results")
    files = sorted(results_dir.glob("*.json"), reverse=True)
    if not files:
        print("ERROR: No eval result files found in eval_results/", file=sys.stderr)
        sys.exit(1)
    return files[0]


def check(data: dict, path: Path) -> None:
    summary = data.get("summary", {})
    results = data.get("results", [])
    meta = data.get("meta", {})

    avg_recall = summary.get("avg_recall", 0.0)
    pass_rate_str = summary.get("pass_rate", "0/0")
    passed, total = (int(x) for x in pass_rate_str.split("/"))
    pass_fraction = passed / total if total > 0 else 0.0
    zero_recall = [r for r in results if r.get("recall", 0.0) == 0.0]

    print(f"\n{'='*60}")
    print(f"  Eval Regression Check")
    print(f"  File      : {path}")
    print(f"  Timestamp : {meta.get('timestamp', 'unknown')}")
    print(f"  Mode      : {meta.get('mode', 'unknown')}")
    print(f"  Prompt    : {data.get('prompt_version', 'unknown')}")
    print(f"{'='*60}")
    print(f"\n  Avg recall   : {avg_recall:.3f}  (threshold: >= {RECALL_THRESHOLD})")
    print(f"  Pass rate    : {pass_rate_str}  (threshold: >= {PASS_RATE_THRESHOLD:.0%})")
    print(f"  Zero-recall  : {len(zero_recall)}  (allowed: <= {ZERO_RECALL_ALLOWED})")

    failures = []

    if avg_recall < RECALL_THRESHOLD:
        failures.append(
            f"avg_recall {avg_recall:.3f} is below threshold {RECALL_THRESHOLD}"
        )

    if pass_fraction < PASS_RATE_THRESHOLD:
        failures.append(
            f"pass_rate {pass_rate_str} ({pass_fraction:.0%}) is below threshold {PASS_RATE_THRESHOLD:.0%}"
        )

    if len(zero_recall) > ZERO_RECALL_ALLOWED:
        cases = ", ".join(f"{r['id']}({r['category']})" for r in zero_recall)
        failures.append(f"{len(zero_recall)} test case(s) scored 0.0 recall: {cases}")

    # Per-case detail
    print(f"\n  Per-case results:")
    for r in results:
        status = "✓" if r.get("passed") else "✗"
        error = f"  ← {r.get('error')}" if r.get("error") else ""
        print(
            f"    {status} [{r['id']}] {r['category']:<24} "
            f"recall={r['recall']:.2f}  {r['latency_ms']:>6}ms  [{r['model']}]{error}"
        )

    print()

    if failures:
        print(f"  {'='*58}")
        print(f"  ✗ REGRESSION DETECTED — {len(failures)} check(s) failed:")
        for i, f in enumerate(failures, 1):
            print(f"    {i}. {f}")
        print(f"  {'='*58}\n")
        sys.exit(1)
    else:
        print(f"  ✓ All regression checks passed\n")
        sys.exit(0)


def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.exists():
            print(f"ERROR: File not found: {path}", file=sys.stderr)
            sys.exit(1)
    else:
        path = latest_result()
        print(f"No file specified — using latest: {path}")

    data = load_result(path)
    check(data, path)


if __name__ == "__main__":
    main()
