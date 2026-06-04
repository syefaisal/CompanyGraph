"""
Stateless utility helpers extracted from api.py.

These are pure functions with no dependency on the FastAPI app, the Anthropic
client, or the live metrics state — which keeps them independently testable
(see tests/test_unit_safety.py) and reusable across endpoints.

Contents:
  • Prompt loading      — _load_prompts
  • Graph serialization — _format_graph
  • Input safety        — _check_injection (prompt-injection defence)
  • Output safety       — _scan_output (PII detection + redaction)
"""
import re as _re
from pathlib import Path
from typing import Optional

import yaml as _yaml


# ── Prompt versioning ─────────────────────────────────────────────────────────

def _load_prompts(version: str) -> dict:
    """Load prompts/<version>.yaml; raise a helpful error listing available versions."""
    path = Path(__file__).parent / "prompts" / f"{version}.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt version '{version}' not found. "
            f"Expected: prompts/{version}.yaml  |  "
            f"Available: {[p.stem for p in (Path(__file__).parent / 'prompts').glob('*.yaml')]}"
        )
    with open(path, encoding="utf-8") as f:
        data = _yaml.safe_load(f)
    return data


# ── Graph serialization ───────────────────────────────────────────────────────

def _format_graph(graph: dict) -> str:
    """Serialize a {nodes, relationships} graph dict into the plain-text block
    that goes into the cached system prompt."""
    lines = ["=== NODES ==="]
    for n in graph["nodes"]:
        props = {k: v for k, v in n.items() if k not in ("id", "label", "_labels")}
        lines.append(
            f"[{n['label']}] id={n['id']} | "
            + " | ".join(f"{k}={v}" for k, v in props.items() if v)
        )
    lines.append("\n=== RELATIONSHIPS ===")
    for r in graph["relationships"]:
        lines.append(f"{r['from_id']} --[{r['type']}]--> {r['to_id']}")
    return "\n".join(lines)


# ── Prompt injection defence ─────────────────────────────────────────────────
# Guards both /query and /query/agent before any LLM call is made.
# Checks: max length (500 chars) + pattern match against known injection families.
# Callers increment _metrics["safety_events"] and return HTTP 400 on a hit.
# The rejected question is never forwarded to the LLM or logged to LangSmith.

MAX_QUESTION_LENGTH = 500

_INJECTION_PATTERNS: list[tuple[str, str]] = [
    # Instruction override
    (r"ignore\s+(all\s+)?(previous|prior|above|these)\s+instructions?",
     "instruction_override"),
    (r"disregard\s+(all\s+)?(the\s+)?(previous|prior|above|these|your)\s+(instructions?|rules?|guidelines?)",
     "instruction_override"),
    (r"forget\s+(all\s+)?(previous|prior|above|your)\s+instructions?",
     "instruction_override"),
    (r"override\s+(your|the|all)\s+(instructions?|directives?|rules?)",
     "instruction_override"),
    (r"new\s+(instructions?|rules?|directives?)\s*[:;]",
     "instruction_override"),

    # System prompt extraction
    (r"(reveal|show|print|output|display|repeat)\s+(\w+\s+)?(your|the)?\s*(system|initial|original)?\s*(prompt|instructions?)\b",
     "prompt_extraction"),
    (r"what\s+(is|are)\s+your\s+(system\s+)?(prompt|instructions?|directives?)",
     "prompt_extraction"),
    (r"(tell\s+me|give\s+me)\s+(\w+\s+)?(your|the)?\s*(system|initial|original)?\s*(prompt|instructions?)",
     "prompt_extraction"),

    # Identity / role override
    (r"you\s+are\s+now\s+(a|an|the)\s+\w+",
     "identity_override"),
    (r"pretend\s+(you\s+are|to\s+be)\s+(a|an|the)?",
     "identity_override"),
    (r"roleplay\s+as\s+(a|an|the)?",
     "identity_override"),
    (r"simulate\s+being\s+(a|an|the)?",
     "identity_override"),
    (r"act\s+as\s+(if\s+you\s+(are|were)\s+)?(a|an|the)?\s*(different|unrestricted|unfiltered)",
     "identity_override"),

    # Jailbreak / mode switch keywords
    (r"\bjailbreak\b", "jailbreak"),
    (r"\bdan\s+mode\b", "jailbreak"),
    (r"\bdeveloper\s+mode\b", "jailbreak"),
    (r"\bunrestricted\s+mode\b", "jailbreak"),
    (r"\bgodmode\b", "jailbreak"),

    # Delimiter injection (fake system/user/assistant turns)
    (r"<\s*system\s*>", "delimiter_injection"),
    (r"\[system\]", "delimiter_injection"),
    (r"###\s*system", "delimiter_injection"),
    (r"\bassistant\s*:", "delimiter_injection"),
    (r"\bsystem\s*:", "delimiter_injection"),
]

_COMPILED_PATTERNS: list[tuple[_re.Pattern, str]] = [
    (_re.compile(pat, _re.IGNORECASE), label)
    for pat, label in _INJECTION_PATTERNS
]


def _check_injection(question: str) -> Optional[str]:
    """
    Returns a violation category string if the question looks like a prompt
    injection attempt, or None if it is safe to proceed.
    Never raises — callers decide how to handle the result.
    """
    if len(question) > MAX_QUESTION_LENGTH:
        return f"question_too_long:{len(question)}_chars_max_{MAX_QUESTION_LENGTH}"

    for pattern, label in _COMPILED_PATTERNS:
        if pattern.search(question):
            return label

    return None


# ── Output safety guardrails ─────────────────────────────────────────────────
# Scans LLM output text for PropTech-relevant PII patterns before sending to
# the browser. Detected values are redacted with [REDACTED:<TYPE>]; callers
# record the event in _metrics["output_safety_events"].
#
# Implementation note: the standard /query endpoint buffers the full response
# before emitting so the scan can cover complete token sequences (e.g. a card
# number split across multiple stream chunks). The agent /query/agent endpoint
# already assembles the final answer before emission.

_OUTPUT_PII_PATTERNS: list[tuple[_re.Pattern, str]] = [
    # Social Security Numbers  — NNN-NN-NNNN
    (_re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), "SSN"),

    # Payment card numbers — 16-digit formatted (spaces or dashes)
    (_re.compile(r'\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}\b'), "PAYMENT_CARD"),

    # Payment card numbers — Visa / Mastercard / Amex / Discover (unformatted)
    (_re.compile(
        r'\b(?:4[0-9]{12}(?:[0-9]{3})?'      # Visa 13/16 digits
        r'|5[1-5][0-9]{14}'                    # Mastercard
        r'|3[47][0-9]{13}'                     # Amex
        r'|6(?:011|5[0-9]{2})[0-9]{12})\b'    # Discover
    ), "PAYMENT_CARD"),

    # US bank routing numbers — 9-digit ABA format starting with 0-3
    (_re.compile(r'\b(?:0[0-9]{8}|[1-3][0-9]{8})\b'), "ROUTING_NUMBER"),

    # External email addresses — flag addresses outside @meridianpg.com
    (_re.compile(
        r'\b[A-Za-z0-9._%+\-]+@(?!meridianpg\.com\b)[A-Za-z0-9.\-]+\.[A-Za-z]{2,7}\b'
    ), "EXTERNAL_EMAIL"),
]


def _scan_output(text: str) -> tuple[str, list[str]]:
    """
    Scan output text for PII. Returns (redacted_text, [violation_types]).
    If no PII found: (original_text, []).
    Detected values are replaced with [REDACTED:<TYPE>].
    """
    violations: list[str] = []
    result = text
    for pattern, label in _OUTPUT_PII_PATTERNS:
        if pattern.search(result):
            violations.append(label)
            result = pattern.sub(f"[REDACTED:{label}]", result)
    return result, violations
