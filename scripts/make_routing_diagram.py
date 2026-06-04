"""
Generate the query-routing / model-selection diagram (PNG):
    docs/model_routing.png

A matplotlib render of the same flow as the Mermaid diagram in the README
(kept local + reproducible — no mermaid CLI / external service needed).
Run:  python scripts/make_routing_diagram.py
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

OUT = Path(__file__).resolve().parent.parent / "docs"

DIRECT = ("#d1fae5", "#059669")   # green  — no LLM
HAIKU  = ("#e0f2fe", "#0284c7")   # sky    — cheap model
SONNET = ("#ede9fe", "#7c3aed")   # violet — capable model
GUARD  = ("#ffe4e6", "#e11d48")   # rose   — safety
IO     = ("#f1f5f9", "#475569")   # slate  — generic i/o
CACHE  = ("#eef2ff", "#6366f1")   # indigo — cached prompt
SSE    = ("#d1fae5", "#059669")   # emerald — stream
DECIS  = ("#ffffff", "#334155")   # white  — decision
INK    = "#0f172a"


def box(ax, x, y, w, h, text, fc, ec, fs=10, weight="normal", fc_text=INK):
    ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h,
                 boxstyle="round,pad=0.02,rounding_size=0.10",
                 linewidth=1.8, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=fc_text, weight=weight, zorder=3)
    return dict(t=(x, y+h/2), b=(x, y-h/2), l=(x-w/2, y), r=(x+w/2, y), x=x, y=y, w=w, h=h)


def diamond(ax, x, y, w, h, text, fs=9.5):
    pts = [(x, y+h/2), (x+w/2, y), (x, y-h/2), (x-w/2, y)]
    ax.add_patch(Polygon(pts, closed=True, linewidth=1.8,
                 edgecolor=DECIS[1], facecolor=DECIS[0], zorder=2))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=INK, zorder=3)
    return dict(t=(x, y+h/2), b=(x, y-h/2), l=(x-w/2, y), r=(x+w/2, y), x=x, y=y)


def arrow(ax, p1, p2, color="#334155", lw=1.9, rad=0.0, label=None, lx=0, ly=0, fs=8.5):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=15,
                 color=color, lw=lw, zorder=1, connectionstyle=f"arc3,rad={rad}"))
    if label:
        mx, my = (p1[0]+p2[0])/2 + lx, (p1[1]+p2[1])/2 + ly
        ax.text(mx, my, label, ha="center", va="center", fontsize=fs, color=color, zorder=5,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))


def legend(ax, items, x, y, dy=0.42):
    for i, (label, (fc, ec)) in enumerate(items):
        yy = y - i*dy
        ax.add_patch(FancyBboxPatch((x, yy-0.13), 0.32, 0.26,
                     boxstyle="round,pad=0.01,rounding_size=0.05",
                     linewidth=1.4, edgecolor=ec, facecolor=fc, zorder=2))
        ax.text(x+0.46, yy, label, ha="left", va="center", fontsize=8.5, color="#334155")


def build():
    fig, ax = plt.subplots(figsize=(9, 11))
    ax.set_xlim(0, 9); ax.set_ylim(0, 13); ax.axis("off")

    ax.text(4.5, 12.6, "Query Routing — Model Selection", ha="center", fontsize=16, weight="bold", color=INK)
    ax.text(4.5, 12.24, "POST /query  ·  classify before calling an LLM", ha="center", fontsize=10, color="#64748b")

    cx = 4.0
    q     = box(ax, cx, 11.4, 3.0, 0.62, "User question  ·  POST /query", *IO, weight="bold", fs=9.5)
    safe  = diamond(ax, cx, 10.1, 2.7, 1.0, "prompt-injection\nguard")
    r400  = box(ax, 7.5, 10.1, 2.2, 0.6, "HTTP 400\nrejected", *GUARD, fs=9)
    direc = diamond(ax, cx, 8.55, 3.0, 1.05, "list / count query?\n(_try_direct_answer)", fs=9)

    d     = box(ax, 1.5, 6.7, 2.5, 1.15, "DIRECT — no LLM\nanswered from Neo4j\n~10 ms · $0", *DIRECT, fs=9, weight="bold")
    route = diamond(ax, cx, 6.95, 2.3, 0.95, "route_query", fs=10)

    s     = box(ax, 6.4, 5.0, 2.6, 1.0, "SONNET\nmulti-hop reasoning", *SONNET, fs=9.5, weight="bold")
    h     = box(ax, 3.4, 5.0, 2.6, 1.0, "HAIKU\nsimple lookup · fast & cheap", *HAIKU, fs=9.2, weight="bold")

    ctx   = box(ax, cx, 3.4, 3.2, 0.78, "Full graph in\ncached system prompt", *CACHE, fs=9)
    ans   = box(ax, cx, 2.0, 3.6, 0.66, "Stream answer (SSE)", *SSE, fs=9.5, weight="bold")

    arrow(ax, q["b"], safe["t"])
    arrow(ax, safe["r"], r400["l"], color=GUARD[1], label="blocked", ly=0.18)
    arrow(ax, safe["b"], direc["t"], label="ok", lx=0.28)
    arrow(ax, direc["l"], d["t"], color=DIRECT[1], rad=0.2, label="yes", lx=-0.2, ly=0.2)
    arrow(ax, direc["b"], route["t"], label="no", lx=0.25)
    arrow(ax, route["l"], h["t"], color=HAIKU[1], rad=0.15,
          label="budget cap ·\nor simple lookup", lx=-0.1, ly=0.35, fs=8)
    arrow(ax, route["r"], s["t"], color=SONNET[1], rad=-0.15,
          label="complexity keyword ·\nor > 12 words", lx=0.1, ly=0.35, fs=8)
    arrow(ax, h["b"], ctx["t"], color=HAIKU[1])
    arrow(ax, s["b"], ctx["t"], color=SONNET[1])
    arrow(ax, ctx["b"], ans["t"])
    arrow(ax, (d["x"], d["y"]-d["h"]/2), ans["l"], color=DIRECT[1], rad=-0.3)

    legend(ax, [("Direct — no LLM", DIRECT), ("Haiku — cheap", HAIKU),
                ("Sonnet — capable", SONNET), ("Safety", GUARD)], 0.3, 1.7)

    fig.tight_layout()
    fig.savefig(OUT / "model_routing.png", dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", OUT / "model_routing.png")


if __name__ == "__main__":
    build()
