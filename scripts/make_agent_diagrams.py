"""
Generate agent-harness diagrams (PNG) for CogniGraph.

  docs/agent_harness_single.png  — single-agent tool-calling loop  (POST /query/agent)
  docs/agent_harness_multi.png   — multi-agent orchestration       (POST /query/orchestrate)

Pure matplotlib (no graphviz). Run:  python scripts/make_agent_diagrams.py
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

OUT = Path(__file__).resolve().parent.parent / "docs"

# ── palette (matches the UI model colors) ─────────────────────────────────────
SONNET = ("#ede9fe", "#7c3aed")   # violet  — capable model
HAIKU  = ("#e0f2fe", "#0284c7")   # sky     — cheap model
GUARD  = ("#ffe4e6", "#e11d48")   # rose    — safety
TOOLS  = ("#fef3c7", "#d97706")   # amber   — tools
DATA   = ("#ccfbf1", "#0f766e")   # teal    — graph / neo4j
IO     = ("#f1f5f9", "#475569")   # slate   — generic i/o
SSE    = ("#d1fae5", "#059669")   # emerald — stream out
LOOP   = ("#eef2ff", "#6366f1")   # indigo  — loop container
INK    = "#0f172a"


def box(ax, x, y, w, h, text, fc, ec, fs=10, weight="normal", rounding=0.10, fc_text=INK, z=2):
    ax.add_patch(FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle=f"round,pad=0.01,rounding_size={rounding}",
        linewidth=1.8, edgecolor=ec, facecolor=fc, zorder=z))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=fc_text,
            weight=weight, zorder=z + 1)
    return dict(c=(x, y), t=(x, y + h / 2), b=(x, y - h / 2),
                l=(x - w / 2, y), r=(x + w / 2, y), w=w, h=h, x=x, y=y)


def arrow(ax, p1, p2, color="#334155", lw=2.0, style="-|>", ls="-", rad=0.0,
          label=None, lx=0, ly=0, fs=8.5):
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle=style, mutation_scale=16, color=color, lw=lw,
        linestyle=ls, zorder=1,
        connectionstyle=f"arc3,rad={rad}"))
    if label:
        mx, my = (p1[0] + p2[0]) / 2 + lx, (p1[1] + p2[1]) / 2 + ly
        ax.text(mx, my, label, ha="center", va="center", fontsize=fs,
                color=color, zorder=5,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))


def legend(ax, items, x, y, dy=0.42):
    for i, (label, (fc, ec)) in enumerate(items):
        yy = y - i * dy
        ax.add_patch(FancyBboxPatch((x, yy - 0.13), 0.34, 0.26,
                     boxstyle="round,pad=0.01,rounding_size=0.05",
                     linewidth=1.4, edgecolor=ec, facecolor=fc, zorder=2))
        ax.text(x + 0.5, yy, label, ha="left", va="center", fontsize=8.5, color="#334155")


# ══════════════════════════════════════════════════════════════════════════════
# 1) SINGLE-AGENT HARNESS
# ══════════════════════════════════════════════════════════════════════════════
def single_agent():
    fig, ax = plt.subplots(figsize=(9.5, 12.5))
    ax.set_xlim(0, 9.5); ax.set_ylim(0, 12.8); ax.axis("off")

    ax.text(4.75, 12.4, "Single-Agent Harness", ha="center", fontsize=17, weight="bold", color=INK)
    ax.text(4.75, 12.02, "POST /query/agent  ·  responder–thinker tool-calling loop",
            ha="center", fontsize=10.5, color="#64748b")

    col = 3.1   # main column
    tcol = 7.4  # tools column

    q  = box(ax, col, 11.2, 3.0, 0.62, "User question", *IO, weight="bold")
    sg = box(ax, col, 10.2, 3.6, 0.62, "Safety guard  ·  _check_injection\n(reject → HTTP 400)", *GUARD, fs=9)
    rt = box(ax, col, 9.2, 3.6, 0.62, "route_query  →  Haiku / Sonnet", *IO, fs=9.5, weight="bold")

    arrow(ax, q["b"], sg["t"]); arrow(ax, sg["b"], rt["t"])

    # loop container
    cx0, cx1, cy0, cy1 = 0.55, 5.65, 2.55, 8.55
    ax.add_patch(FancyBboxPatch((cx0, cy0), cx1 - cx0, cy1 - cy0,
                 boxstyle="round,pad=0.02,rounding_size=0.12",
                 linewidth=1.8, edgecolor=LOOP[1], facecolor=LOOP[0],
                 linestyle=(0, (6, 4)), zorder=0))
    ax.text((cx0 + cx1) / 2, cy1 - 0.28, "AGENT LOOP  —  up to 8 iterations",
            ha="center", fontsize=9.5, weight="bold", color=LOOP[1])

    llm = box(ax, col, 7.45, 3.7, 1.15,
              "Claude  ·  messages.create()\nmodel = routed Haiku/Sonnet\ntools = AGENT_TOOLS (5)\nsystem = AGENT_SYSTEM_PROMPT",
              *SONNET, fs=8.5)
    dec = box(ax, col, 5.75, 2.5, 0.7, "stop_reason ?", "#ffffff", "#334155", fs=9.5, weight="bold")
    ex  = box(ax, col, 4.15, 3.5, 0.78, "_execute_agent_tool()\nrun requested tool(s)", *TOOLS, fs=9)

    arrow(ax, rt["b"], llm["t"])
    arrow(ax, llm["b"], dec["t"])
    arrow(ax, dec["b"], ex["t"], label="tool_use", ly=0.0, lx=-0.55, color=TOOLS[1])
    # loop-back: execute -> back up to LLM (left side, curved)
    arrow(ax, (ex["x"] - ex["w"] / 2, ex["y"]), (llm["x"] - llm["w"] / 2, llm["y"] - 0.2),
          color="#6366f1", rad=-0.55, lw=2.0,
          label="append\ntool_result\n→ next turn", lx=-0.4, ly=0.0, fs=8)

    # tools + data column
    tb = box(ax, tcol, 4.15, 3.3, 1.55,
             "Graph tools (5)\nsearch_graph · get_entity\nfind_path\ntrace_decision_impact\nrun_cypher",
             *TOOLS, fs=8.3)
    db = box(ax, tcol, 2.05, 3.0, 0.66, "graph.py  →  Neo4j", *DATA, fs=9.5, weight="bold")
    arrow(ax, ex["r"], tb["l"], color=TOOLS[1])
    arrow(ax, (tb["x"], tb["y"] - tb["h"] / 2), (db["x"], db["y"] + db["h"] / 2), color=DATA[1], style="<|-|>")

    # exit loop -> PII -> SSE
    pii = box(ax, col, 1.55, 3.6, 0.62, "PII output scan  ·  _scan_output", *GUARD, fs=9)
    out = box(ax, 3.9, 0.62, 6.7, 0.66,
              "SSE stream:  thinking · tool_call · tool_result · text · done", *SSE, fs=9, weight="bold")
    arrow(ax, (col, cy0), pii["t"], label="end_turn", lx=0.7, ly=0.06, color="#334155")
    arrow(ax, pii["b"], (3.9, out["y"] + out["h"] / 2))

    # tracing note
    ax.text(8.9, 7.7, "LangSmith\n@traceable\nwraps every\nLLM turn +\ntool call",
            ha="center", va="center", fontsize=8, color="#6366f1",
            bbox=dict(boxstyle="round,pad=0.4", fc="#eef2ff", ec="#6366f1", lw=1.2))

    legend(ax, [("Sonnet (capable)", SONNET), ("Haiku (cheap)", HAIKU),
                ("Safety", GUARD), ("Tools", TOOLS), ("Graph / Neo4j", DATA)],
           6.55, 11.35)

    fig.tight_layout()
    fig.savefig(OUT / "agent_harness_single.png", dpi=160, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("wrote", OUT / "agent_harness_single.png")


# ══════════════════════════════════════════════════════════════════════════════
# 2) MULTI-AGENT HARNESS
# ══════════════════════════════════════════════════════════════════════════════
def multi_agent():
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_xlim(0, 12); ax.set_ylim(0, 12); ax.axis("off")

    ax.text(6, 11.6, "Multi-Agent Harness", ha="center", fontsize=17, weight="bold", color=INK)
    ax.text(6, 11.22, "POST /query/orchestrate  ·  planner → parallel workers → synthesizer",
            ha="center", fontsize=10.5, color="#64748b")

    q  = box(ax, 6, 10.5, 3.0, 0.6, "User question", *IO, weight="bold")
    sg = box(ax, 6, 9.55, 3.8, 0.6, "Safety guard · _check_injection", *GUARD, fs=9)
    pl = box(ax, 6, 8.5, 4.4, 0.92, "Planner · Sonnet\nforced submit_plan tool", *SONNET, fs=10, weight="bold")
    pn = box(ax, 6, 7.5, 3.6, 0.56, "plan:  N independent sub-questions", *LOOP, fs=9)
    arrow(ax, q["b"], sg["t"]); arrow(ax, sg["b"], pl["t"]); arrow(ax, pl["b"], pn["t"])

    # parallel workers
    wy = 5.7
    wxs = [2.4, 6.0, 9.6]
    ids = ["s1", "s2", "s3"]
    workers = []
    for wx, sid in zip(wxs, ids):
        wbox = box(ax, wx, wy, 3.0, 1.5,
                   f"Worker {sid} · Haiku\n= single-agent harness\nbounded loop (≤5 iters)\nover AGENT_TOOLS",
                   *HAIKU, fs=8.6)
        workers.append(wbox)
        arrow(ax, pn["b"], wbox["t"], rad=0.0, color=HAIKU[1])
    ax.text(6, 6.62, "parallel  ·  asyncio.as_completed", ha="center", fontsize=9,
            weight="bold", color="#0284c7",
            bbox=dict(boxstyle="round,pad=0.2", fc="#e0f2fe", ec="#0284c7", lw=1.0))

    # shared data layer (under workers)
    db = box(ax, 6, 4.05, 8.6, 0.62,
             "each worker's tool loop  →  graph.py  →  Neo4j   (same tools as the single-agent harness)",
             *DATA, fs=9)
    for wbox in workers:
        arrow(ax, wbox["b"], (wbox["x"], db["y"] + db["h"] / 2), color=DATA[1], style="<|-|>", lw=1.6)

    # synthesizer (fan-in)
    syn = box(ax, 6, 2.75, 5.0, 0.95,
              "Synthesizer · Sonnet  (streamed)\nmerge findings — grounded only in worker answers",
              *SONNET, fs=9.5, weight="bold")
    for wbox in workers:
        arrow(ax, (wbox["x"], db["y"] - db["h"] / 2), syn["t"], rad=0.0,
              color="#7c3aed", lw=1.6,
              label=("subagent_result" if wbox is workers[1] else None), ly=0.35)

    pii = box(ax, 6, 1.65, 3.6, 0.58, "PII output scan · _scan_output", *GUARD, fs=9)
    out = box(ax, 6, 0.72, 9.4, 0.62,
              "SSE stream:  plan · subagent_start · subagent_result · synthesis · text · done",
              *SSE, fs=9, weight="bold")
    arrow(ax, syn["b"], pii["t"]); arrow(ax, pii["b"], out["t"])

    # notes
    ax.text(0.25, 8.5,
            "Per-role routing\n(cost lever):\n• Planner — Sonnet\n• Workers — Haiku ×N\n• Synth   — Sonnet",
            ha="left", va="center", fontsize=8.4, color="#334155",
            bbox=dict(boxstyle="round,pad=0.4", fc="#f8fafc", ec="#cbd5e1", lw=1.2))
    ax.text(11.75, 8.5,
            "No framework\n(no LangGraph /\nCrewAI / AutoGen)\n— native Anthropic\nSDK + asyncio",
            ha="right", va="center", fontsize=8.4, color="#6366f1",
            bbox=dict(boxstyle="round,pad=0.4", fc="#eef2ff", ec="#6366f1", lw=1.2))

    fig.tight_layout()
    fig.savefig(OUT / "agent_harness_multi.png", dpi=160, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("wrote", OUT / "agent_harness_multi.png")


if __name__ == "__main__":
    single_agent()
    multi_agent()
