"""
Cross-functional knowledge graph query tests.

Query 1 — Root Cause & Blast Radius Analysis
  Given any product in a non-active state, trace backwards to the decision that
  caused it, who made it, and forwards to every customer / workflow / person
  downstream. Rank by total blast radius.

Query 2 — Updating Knowledge Context via Chat
  Simulate a real chat update: "We just closed PharmaGlobal — enterprise
  healthcare, APAC, using Analytics + Connect. Sarah approved the expansion."
  Add all entities/relationships, then re-query the graph to verify the new
  context is reflected everywhere (customer profile, decision impact, workflow
  team ownership, product customer list).

Query 3 — Strategic Risk: Workflow Chain Failure & Single Points of Failure
  For every workflow that sits in a dependency chain, find the full upstream/
  downstream chain, every decision that has touched any workflow in that chain,
  every person in the chain, and every product that would be blocked if the
  chain broke. Compute a risk score = (chain depth) × (distinct people) ×
  (distinct products). Also find org-level single points of failure: people
  whose removal would disconnect the most workflows, decisions, and products.
"""

import json
from graph import run, create_node, create_relationship, get_node_with_connections

DIVIDER = "=" * 70


def header(title: str):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def sub(title: str):
    print(f"\n── {title} ──")


# ─────────────────────────────────────────────────────────────────────────────
# QUERY 1: Root Cause & Blast Radius Analysis
# ─────────────────────────────────────────────────────────────────────────────

def query1_root_cause_and_blast_radius():
    header("QUERY 1 · Root Cause & Blast Radius Analysis")

    print("""
Goal: For each non-active product, find:
  • which decision changed its fate (root cause)
  • who made that decision (accountability)
  • which customers are directly exposed (customer impact)
  • which workflows touch the product (operational impact)
  • which other products those workflow-people also own (ripple risk)
  • a total blast-radius score = customers + workflows + downstream products
""")

    # ── Step 1: Decision → affected non-active product ───────────────────────
    sub("Step 1 · Decision → non-active product (direct link)")
    rows = run("""
        MATCH (d:Decision)-[:AFFECTS]->(pr:Product)
        WHERE pr.status IN ['deprecated', 'beta']
        MATCH (maker:Person)-[:MADE]->(d)
        RETURN d.name          AS decision,
               d.date          AS date,
               d.rationale     AS rationale,
               maker.name      AS decision_maker,
               maker.role      AS maker_role,
               pr.name         AS product,
               pr.status       AS status
        ORDER BY d.date DESC
    """)
    for r in rows:
        print(f"\n  Decision  : {r['decision']} ({r['date']})")
        print(f"  Made by   : {r['decision_maker']} ({r['maker_role']})")
        print(f"  Product   : {r['product']}  [status: {r['status']}]")
        print(f"  Rationale : {r['rationale']}")

    # ── Step 2: Full blast radius per decision ───────────────────────────────
    sub("Step 2 · Blast radius — customers, workflows, downstream people & products")
    rows = run("""
        MATCH (d:Decision)-[:AFFECTS]->(pr:Product)
        WHERE pr.status IN ['deprecated', 'beta']
        MATCH (maker:Person)-[:MADE]->(d)

        // customers directly exposed
        OPTIONAL MATCH (c:Customer)-[:USES]->(pr)

        // workflows that produce this product
        OPTIONAL MATCH (w:Workflow)-[:PRODUCES]->(pr)

        // people involved in those workflows
        OPTIONAL MATCH (w)-[:INVOLVES]->(wp:Person)

        // OTHER products those people work on (ripple risk)
        OPTIONAL MATCH (wp)-[:WORKS_ON]->(rp:Product)
        WHERE rp.id <> pr.id

        WITH d, maker, pr,
             collect(DISTINCT c.name)  AS affected_customers,
             collect(DISTINCT w.name)  AS affected_workflows,
             collect(DISTINCT wp.name) AS people_in_workflows,
             collect(DISTINCT rp.name) AS ripple_risk_products

        RETURN d.name                         AS decision,
               maker.name                     AS decision_maker,
               pr.name                        AS product,
               pr.status                      AS status,
               affected_customers,
               affected_workflows,
               people_in_workflows,
               ripple_risk_products,
               size(affected_customers)
               + size(affected_workflows)
               + size(people_in_workflows)
               + size(ripple_risk_products)   AS blast_radius
        ORDER BY blast_radius DESC
    """)
    for r in rows:
        print(f"\n  {'─'*60}")
        print(f"  Decision        : {r['decision']}")
        print(f"  Decision maker  : {r['decision_maker']}")
        print(f"  Affected product: {r['product']}  [{r['status']}]")
        print(f"  Customers at risk ({len(r['affected_customers'])}): {r['affected_customers'] or '(none)'}")
        print(f"  Workflows hit   ({len(r['affected_workflows'])}): {r['affected_workflows'] or '(none)'}")
        print(f"  People in chain ({len(r['people_in_workflows'])}): {r['people_in_workflows'] or '(none)'}")
        print(f"  Ripple products ({len(r['ripple_risk_products'])}): {r['ripple_risk_products'] or '(none)'}")
        print(f"  ★ BLAST RADIUS  : {r['blast_radius']}")

    # ── Step 3: Multi-hop path — Customer → affected Product ─────────────────
    sub("Step 3 · Shortest path: HealthFirst → Nexus Mobile (cross-functional chain)")
    rows = run("""
        MATCH p = shortestPath(
          (c:Customer {name: 'HealthFirst'})-[*..8]-(pr:Product {name: 'Nexus Mobile'})
        )
        RETURN [n IN nodes(p)    | {name: n.name, label: labels(n)[0]}] AS path_nodes,
               [r IN relationships(p) | type(r)]                         AS path_rels,
               length(p)                                                  AS hops
    """)
    if rows:
        r = rows[0]
        print(f"\n  HealthFirst ──({r['hops']} hops)──▶ Nexus Mobile")
        path_str = ""
        for i, node in enumerate(r['path_nodes']):
            path_str += f"[{node['label']}] {node['name']}"
            if i < len(r['path_rels']):
                path_str += f"  ──{r['path_rels'][i]}──▶  "
        print(f"\n  {path_str}")
    else:
        print("  (no path found)")

    print(f"\n{'─'*70}")
    print("  ✓ Query 1 complete")


# ─────────────────────────────────────────────────────────────────────────────
# QUERY 2: Updating Knowledge Context via Chat
# ─────────────────────────────────────────────────────────────────────────────

def query2_update_via_chat():
    header("QUERY 2 · Updating Knowledge Context via Chat")

    print("""
Simulated chat input:
  \"We just closed PharmaGlobal — 3-year enterprise deal, healthcare, APAC.
  They'll use Nexus Analytics and Nexus Connect. Sarah Chen approved the
  expansion; it's a direct result of the Enter Healthcare Market decision.
  Aisha will run their onboarding. Add them and show me the full picture.\"

Steps:
  1  Add PharmaGlobal as a Customer node
  2  Connect PharmaGlobal → Nexus Analytics  (USES)
  3  Connect PharmaGlobal → Nexus Connect    (USES)
  4  Link Enter Healthcare Market decision   (AFFECTS → PharmaGlobal)
  5  Add PharmaGlobal to Customer Onboarding workflow (INVOLVES)
  6  Verify: customer profile with all connections
  7  Verify: decision impact now includes PharmaGlobal
  8  Verify: Aisha Okafor's workflow shows new customer context
  9  Verify: Nexus Connect customer list updated
""")

    # ── Step 1–5: Write operations ───────────────────────────────────────────
    sub("Steps 1–5 · Writing new context to the graph")

    existing = run("MATCH (n:Customer {id: 'c6'}) RETURN n.name AS name")
    if existing:
        print(f"  [skip] PharmaGlobal already exists from a previous run → proceeding to verification")
    else:
        pharma = create_node("Customer", {
            "id": "c6",
            "name": "PharmaGlobal",
            "industry": "Healthcare",
            "tier": "enterprise",
            "region": "APAC",
            "arr_usd": 195000,
            "since": "2026-05-21",
        })
        print(f"  [+] Customer created: {pharma['name']}  (id={pharma['id']})")

        create_relationship("c6", "pr1", "USES")
        print("  [+] PharmaGlobal  ──USES──▶  Nexus Analytics")

        create_relationship("c6", "pr3", "USES")
        print("  [+] PharmaGlobal  ──USES──▶  Nexus Connect")

        create_relationship("d2", "c6", "AFFECTS")
        print("  [+] Enter Healthcare Market  ──AFFECTS──▶  PharmaGlobal")

        create_relationship("w1", "c6", "INVOLVES")
        print("  [+] Customer Onboarding  ──INVOLVES──▶  PharmaGlobal")

    # ── Step 6: Full customer profile ────────────────────────────────────────
    sub("Step 6 · Verify: PharmaGlobal full profile in graph")
    node = get_node_with_connections("c6")
    props = {k: v for k, v in node.items() if k not in ("_labels", "connections")}
    print(f"\n  {json.dumps(props, indent=4)}")
    print(f"\n  Connections ({len(node['connections'])}):")
    for c in node["connections"]:
        arrow = "──▶" if c["direction"] == "out" else "◀──"
        print(f"    {arrow} [{c['rel_type']}] {c['neighbor_name']}  ({', '.join(c['neighbor_labels'])})")

    # ── Step 7: Decision impact now includes PharmaGlobal ────────────────────
    sub("Step 7 · Verify: 'Enter Healthcare Market' impact includes new customer")
    rows = run("""
        MATCH (d:Decision {id: 'd2'})-[r*1..2]-(m)
        WHERE m.id <> 'd2'
        RETURN DISTINCT labels(m)[0] AS label, m.name AS name,
               min(size(r)) AS hops
        ORDER BY hops, label
    """)
    print(f"\n  Decision: Enter Healthcare Market — {len(rows)} entities in blast radius:")
    for r in rows:
        marker = "  ◀── NEW" if r["name"] == "PharmaGlobal" else ""
        print(f"    hops={r['hops']}  [{r['label']}] {r['name']}{marker}")

    # ── Step 8: Aisha's workflow context ─────────────────────────────────────
    sub("Step 8 · Verify: Customer Onboarding workflow now involves PharmaGlobal")
    rows = run("""
        MATCH (w:Workflow {id: 'w1'})-[r]-(m)
        RETURN type(r) AS rel, labels(m)[0] AS label, m.name AS name,
               CASE WHEN startNode(r).id = 'w1' THEN 'out' ELSE 'in' END AS dir
        ORDER BY label, name
    """)
    print(f"\n  Customer Onboarding connections ({len(rows)}):")
    for r in rows:
        arrow = "──▶" if r["dir"] == "out" else "◀──"
        print(f"    [{r['label']}] {r['name']}  {arrow}  [{r['rel']}]")

    # ── Step 9: Nexus Connect customer list ───────────────────────────────────
    sub("Step 9 · Verify: Nexus Connect now shows PharmaGlobal as customer")
    rows = run("""
        MATCH (c:Customer)-[:USES]->(pr:Product {id: 'pr3'})
        RETURN c.name AS customer, c.tier AS tier, c.region AS region, c.arr_usd AS arr
        ORDER BY c.arr_usd DESC
    """)
    print(f"\n  Nexus Connect customers ({len(rows)}):")
    for r in rows:
        marker = "  ◀── NEW" if r["customer"] == "PharmaGlobal" else ""
        print(f"    {r['customer']}  [{r['tier']} / {r['region']}]  ARR=${r['arr']:,}{marker}")

    print(f"\n{'─'*70}")
    print("  ✓ Query 2 complete — graph context updated and verified")


# ─────────────────────────────────────────────────────────────────────────────
# QUERY 3: Strategic Risk — Workflow Chain Failure & Single Points of Failure
# ─────────────────────────────────────────────────────────────────────────────

def query3_strategic_risk():
    header("QUERY 3 · Strategic Risk: Workflow Chain Failure & Single Points of Failure")

    print("""
Goal: Identify where the company is fragile.
  Part A — Workflow dependency chains: for each chain, find every person
           involved, every decision that has touched the chain, every product
           at stake, and compute a chain-risk score.
  Part B — People as single points of failure: rank by influence score
           (decisions made + workflows owned + workflows involved in +
           products contributed). Flag people whose removal would create
           the most orphaned workflows/decisions.
""")

    # ── Part A: Workflow chain analysis ──────────────────────────────────────
    sub("Part A · Workflow dependency chains — full cross-functional context")
    rows = run("""
        // Find every workflow that is upstream in a dependency chain
        MATCH chain = (leaf:Workflow)-[:DEPENDS_ON*1..5]->(root:Workflow)
        WHERE NOT (root)-[:DEPENDS_ON]->()          // root has no further deps

        WITH leaf, root,
             [w IN nodes(chain) | w.name]            AS chain_names,
             length(chain)                            AS chain_depth,
             nodes(chain)                             AS chain_nodes

        // All people involved in any workflow in the chain
        UNWIND chain_nodes AS w
        OPTIONAL MATCH (w)-[:INVOLVES]->(person:Person)
        OPTIONAL MATCH (person)-[:OWNS]->(w)

        // Decisions that have affected any workflow in the chain
        OPTIONAL MATCH (d:Decision)-[:AFFECTS]->(w)

        // Products produced by any workflow in the chain
        OPTIONAL MATCH (w)-[:PRODUCES]->(pr:Product)

        WITH leaf.name                               AS leaf_workflow,
             root.name                               AS root_workflow,
             chain_depth,
             chain_names,
             collect(DISTINCT person.name)           AS all_people,
             collect(DISTINCT d.name)                AS affecting_decisions,
             collect(DISTINCT pr.name)               AS products_at_stake

        WITH leaf_workflow, root_workflow, chain_depth, chain_names,
             all_people, affecting_decisions, products_at_stake,
             chain_depth
             * CASE WHEN size(all_people) = 0        THEN 1 ELSE size(all_people) END
             * CASE WHEN size(products_at_stake) = 0 THEN 1 ELSE size(products_at_stake) END
             AS risk_score

        RETURN leaf_workflow, root_workflow, chain_depth,
               chain_names, all_people,
               affecting_decisions, products_at_stake, risk_score
        ORDER BY risk_score DESC
    """)

    for r in rows:
        chain_str = " ──DEPENDS_ON──▶ ".join(r["chain_names"])
        print(f"\n  Chain   : {chain_str}")
        print(f"  Depth   : {r['chain_depth']} hops  (leaf → root)")
        print(f"  People  ({len(r['all_people'])}): {r['all_people'] or '(none)'}")
        print(f"  Decisions affecting this chain ({len(r['affecting_decisions'])}): {r['affecting_decisions'] or '(none)'}")
        print(f"  Products at stake ({len(r['products_at_stake'])}): {r['products_at_stake'] or '(none)'}")
        print(f"  ★ RISK SCORE: {r['risk_score']}")

    # ── Part B: Single points of failure ─────────────────────────────────────
    sub("Part B · Single points of failure — people by influence score")
    rows = run("""
        MATCH (p:Person)
        OPTIONAL MATCH (p)-[:MADE]->(d:Decision)
        OPTIONAL MATCH (p)-[:OWNS]->(owned_w:Workflow)
        OPTIONAL MATCH (involved_w:Workflow)-[:INVOLVES]->(p)
        OPTIONAL MATCH (p)-[:WORKS_ON]->(pr:Product)

        WITH p,
             count(DISTINCT d)          AS decisions_made,
             count(DISTINCT owned_w)    AS workflows_owned,
             count(DISTINCT involved_w) AS workflows_involved,
             count(DISTINCT pr)         AS products_contributed,
             collect(DISTINCT d.name)   AS decision_names,
             collect(DISTINCT owned_w.name)  AS owned_workflow_names,
             collect(DISTINCT pr.name)  AS product_names

        WITH p, decisions_made, workflows_owned, workflows_involved,
             products_contributed, decision_names, owned_workflow_names, product_names,
             decisions_made + workflows_owned + workflows_involved + products_contributed
             AS influence_score

        WHERE influence_score > 0
        RETURN p.name          AS person,
               p.role          AS role,
               p.department    AS department,
               decisions_made,
               workflows_owned,
               workflows_involved,
               products_contributed,
               influence_score,
               decision_names,
               owned_workflow_names,
               product_names
        ORDER BY influence_score DESC
    """)

    print(f"\n  {'Person':<22} {'Role':<28} {'Dec':>4} {'Own':>4} {'Inv':>4} {'Prd':>4}  {'Score':>6}")
    print(f"  {'─'*22} {'─'*28} {'─'*4} {'─'*4} {'─'*4} {'─'*4}  {'─'*6}")
    for r in rows:
        print(
            f"  {r['person']:<22} {r['role']:<28} "
            f"{r['decisions_made']:>4} {r['workflows_owned']:>4} "
            f"{r['workflows_involved']:>4} {r['products_contributed']:>4}  "
            f"{r['influence_score']:>6}"
        )

    # Detail top 2 SPOFs
    sub("Part B · Detail: top 2 highest-influence people")
    for r in rows[:2]:
        print(f"\n  {r['person']}  [{r['role']}]  influence={r['influence_score']}")
        if r["decision_names"]:
            print(f"    Decisions made      : {r['decision_names']}")
        if r["owned_workflow_names"]:
            print(f"    Workflows owned     : {r['owned_workflow_names']}")
        if r["product_names"]:
            print(f"    Products contributed: {r['product_names']}")

        # What becomes orphaned if they leave
        orphan = run("""
            MATCH (p:Person {name: $name})
            MATCH (p)-[:OWNS]->(w:Workflow)
            OPTIONAL MATCH (other:Person)-[:OWNS]->(w)
            WHERE other.id <> p.id
            WITH w, count(other) AS other_owners
            WHERE other_owners = 0
            RETURN w.name AS orphaned_workflow
        """, {"name": r["person"]})
        if orphan:
            print(f"    ⚠ Orphaned workflows if {r['person']} leaves: {[o['orphaned_workflow'] for o in orphan]}")
        else:
            print(f"    ✓ All owned workflows have at least one other owner")

    # ── Part C: Cross-entity "bus factor" summary ────────────────────────────
    sub("Part C · Bus factor summary — workflows with only one owner")
    rows = run("""
        MATCH (w:Workflow)
        OPTIONAL MATCH (p:Person)-[:OWNS]->(w)
        WITH w, collect(p.name) AS owners
        RETURN w.name AS workflow,
               size(owners) AS owner_count,
               owners
        ORDER BY owner_count ASC
    """)
    print(f"\n  {'Workflow':<30} {'Owners':>7}  {'Owner names'}")
    print(f"  {'─'*30} {'─'*7}  {'─'*30}")
    for r in rows:
        risk_flag = "  ⚠  SINGLE OWNER" if r["owner_count"] == 1 else ""
        print(f"  {r['workflow']:<30} {r['owner_count']:>7}  {r['owners']}{risk_flag}")

    print(f"\n{'─'*70}")
    print("  ✓ Query 3 complete")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    query1_root_cause_and_blast_radius()
    query2_update_via_chat()
    query3_strategic_risk()
    print(f"\n{DIVIDER}")
    print("  ALL QUERIES COMPLETE")
    print(DIVIDER)
