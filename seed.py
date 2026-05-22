"""
Seed the knowledge graph with a realistic fictional company: Nexus Corp.
Run: python seed.py
"""
from graph import run, get_driver

CYPHER_SETUP = """
CREATE CONSTRAINT person_id IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT product_id IF NOT EXISTS FOR (n:Product) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (n:Customer) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT workflow_id IF NOT EXISTS FOR (n:Workflow) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (n:Decision) REQUIRE n.id IS UNIQUE;
"""

SEED_QUERIES = [
    # ── People ──────────────────────────────────────────────────────────────────
    """MERGE (n:Person {id: 'p1'}) SET n += {
        name: 'Sarah Chen', role: 'CEO', department: 'Executive',
        email: 'sarah@nexuscorp.io', tenure_years: 6
    }""",
    """MERGE (n:Person {id: 'p2'}) SET n += {
        name: 'Marcus Rivera', role: 'CTO', department: 'Engineering',
        email: 'marcus@nexuscorp.io', tenure_years: 5
    }""",
    """MERGE (n:Person {id: 'p3'}) SET n += {
        name: 'Priya Patel', role: 'VP Product', department: 'Product',
        email: 'priya@nexuscorp.io', tenure_years: 3
    }""",
    """MERGE (n:Person {id: 'p4'}) SET n += {
        name: 'Alex Kim', role: 'Senior Engineer', department: 'Engineering',
        email: 'alex@nexuscorp.io', tenure_years: 4
    }""",
    """MERGE (n:Person {id: 'p5'}) SET n += {
        name: 'Jordan Lee', role: 'Engineer', department: 'Engineering',
        email: 'jordan@nexuscorp.io', tenure_years: 2
    }""",
    """MERGE (n:Person {id: 'p6'}) SET n += {
        name: 'Diana Santos', role: 'Head of Sales', department: 'Sales',
        email: 'diana@nexuscorp.io', tenure_years: 4
    }""",
    """MERGE (n:Person {id: 'p7'}) SET n += {
        name: 'Tom Mitchell', role: 'Marketing Lead', department: 'Marketing',
        email: 'tom@nexuscorp.io', tenure_years: 3
    }""",
    """MERGE (n:Person {id: 'p8'}) SET n += {
        name: 'Aisha Okafor', role: 'Customer Success Manager', department: 'Customer Success',
        email: 'aisha@nexuscorp.io', tenure_years: 2
    }""",

    # ── Products ─────────────────────────────────────────────────────────────────
    """MERGE (n:Product {id: 'pr1'}) SET n += {
        name: 'Nexus Analytics', category: 'BI Dashboard', status: 'active',
        version: '4.2', mrr_usd: 180000
    }""",
    """MERGE (n:Product {id: 'pr2'}) SET n += {
        name: 'Nexus API Platform', category: 'API Gateway', status: 'active',
        version: '2.8', mrr_usd: 95000
    }""",
    """MERGE (n:Product {id: 'pr3'}) SET n += {
        name: 'Nexus Connect', category: 'Data Connector', status: 'beta',
        version: '0.9', mrr_usd: 12000
    }""",
    """MERGE (n:Product {id: 'pr4'}) SET n += {
        name: 'Nexus Mobile', category: 'Mobile App', status: 'deprecated',
        version: '1.5', mrr_usd: 0
    }""",

    # ── Customers ────────────────────────────────────────────────────────────────
    """MERGE (n:Customer {id: 'c1'}) SET n += {
        name: 'TechFlow Inc', industry: 'Technology', tier: 'enterprise',
        region: 'North America', arr_usd: 240000, since: '2021-03-15'
    }""",
    """MERGE (n:Customer {id: 'c2'}) SET n += {
        name: 'RetailPro Corp', industry: 'Retail', tier: 'enterprise',
        region: 'North America', arr_usd: 180000, since: '2022-01-10'
    }""",
    """MERGE (n:Customer {id: 'c3'}) SET n += {
        name: 'HealthFirst', industry: 'Healthcare', tier: 'mid-market',
        region: 'North America', arr_usd: 72000, since: '2023-07-01'
    }""",
    """MERGE (n:Customer {id: 'c4'}) SET n += {
        name: 'StartupX', industry: 'Fintech', tier: 'smb',
        region: 'Europe', arr_usd: 18000, since: '2024-02-20'
    }""",
    """MERGE (n:Customer {id: 'c5'}) SET n += {
        name: 'GlobalShip Ltd', industry: 'Logistics', tier: 'enterprise',
        region: 'APAC', arr_usd: 210000, since: '2022-09-05'
    }""",

    # ── Workflows ────────────────────────────────────────────────────────────────
    """MERGE (n:Workflow {id: 'w1'}) SET n += {
        name: 'Customer Onboarding', type: 'customer-facing', status: 'active',
        avg_duration_days: 14, description: 'End-to-end process for new customer activation'
    }""",
    """MERGE (n:Workflow {id: 'w2'}) SET n += {
        name: 'Sales Pipeline', type: 'revenue', status: 'active',
        avg_duration_days: 45, description: 'Lead qualification through contract close'
    }""",
    """MERGE (n:Workflow {id: 'w3'}) SET n += {
        name: 'Bug Triage', type: 'engineering', status: 'active',
        avg_duration_days: 3, description: 'Incoming bug classification, assignment, and resolution'
    }""",
    """MERGE (n:Workflow {id: 'w4'}) SET n += {
        name: 'Feature Release', type: 'engineering', status: 'active',
        avg_duration_days: 21, description: 'Design → build → QA → ship cycle for product features'
    }""",
    """MERGE (n:Workflow {id: 'w5'}) SET n += {
        name: 'Data Migration', type: 'engineering', status: 'active',
        avg_duration_days: 7, description: 'Moving customer data between environments or product versions'
    }""",
    """MERGE (n:Workflow {id: 'w6'}) SET n += {
        name: 'Quarterly Planning', type: 'strategic', status: 'active',
        avg_duration_days: 10, description: 'OKR setting, roadmap prioritization, and resource allocation'
    }""",

    # ── Decisions ────────────────────────────────────────────────────────────────
    """MERGE (n:Decision {id: 'd1'}) SET n += {
        name: 'Deprecate Nexus Mobile', title: 'Sunset the mobile app product line',
        date: '2024-09-01', outcome: 'approved', rationale: 'Low adoption, high maintenance cost, resources redirected to API platform'
    }""",
    """MERGE (n:Decision {id: 'd2'}) SET n += {
        name: 'Enter Healthcare Market', title: 'Expand sales motion into healthcare vertical',
        date: '2023-06-15', outcome: 'approved', rationale: 'Strong pipeline signal; HealthFirst pilot exceeded targets'
    }""",
    """MERGE (n:Decision {id: 'd3'}) SET n += {
        name: 'Migrate to Kubernetes', title: 'Move all services from EC2 to Kubernetes',
        date: '2024-01-10', outcome: 'approved', rationale: 'Needed for autoscaling to support enterprise SLAs'
    }""",
    """MERGE (n:Decision {id: 'd4'}) SET n += {
        name: 'Introduce Freemium Tier', title: 'Add a free tier to the API Platform',
        date: '2024-11-20', outcome: 'approved', rationale: 'PLG strategy to grow developer adoption and top-of-funnel'
    }""",
    """MERGE (n:Decision {id: 'd5'}) SET n += {
        name: 'GDPR Compliance Overhaul', title: 'Full audit and remediation of data handling for EU compliance',
        date: '2024-03-05', outcome: 'approved', rationale: 'Legal requirement triggered by EU customer expansion'
    }""",
    """MERGE (n:Decision {id: 'd6'}) SET n += {
        name: 'Partner with DataVault', title: 'Sign strategic data-sharing partnership with DataVault',
        date: '2025-01-12', outcome: 'approved', rationale: 'Expands Nexus Connect data sources by 3x without in-house build'
    }""",

    # ── Relationships: People → Products (WORKS_ON) ───────────────────────────
    "MATCH (a:Person {id:'p2'}), (b:Product {id:'pr1'}) MERGE (a)-[:WORKS_ON]->(b)",
    "MATCH (a:Person {id:'p2'}), (b:Product {id:'pr2'}) MERGE (a)-[:WORKS_ON]->(b)",
    "MATCH (a:Person {id:'p3'}), (b:Product {id:'pr1'}) MERGE (a)-[:WORKS_ON]->(b)",
    "MATCH (a:Person {id:'p3'}), (b:Product {id:'pr2'}) MERGE (a)-[:WORKS_ON]->(b)",
    "MATCH (a:Person {id:'p3'}), (b:Product {id:'pr3'}) MERGE (a)-[:WORKS_ON]->(b)",
    "MATCH (a:Person {id:'p4'}), (b:Product {id:'pr1'}) MERGE (a)-[:WORKS_ON]->(b)",
    "MATCH (a:Person {id:'p4'}), (b:Product {id:'pr2'}) MERGE (a)-[:WORKS_ON]->(b)",
    "MATCH (a:Person {id:'p5'}), (b:Product {id:'pr2'}) MERGE (a)-[:WORKS_ON]->(b)",
    "MATCH (a:Person {id:'p5'}), (b:Product {id:'pr3'}) MERGE (a)-[:WORKS_ON]->(b)",

    # ── Relationships: People → Decisions (MADE) ─────────────────────────────
    "MATCH (a:Person {id:'p1'}), (b:Decision {id:'d2'}) MERGE (a)-[:MADE]->(b)",
    "MATCH (a:Person {id:'p1'}), (b:Decision {id:'d4'}) MERGE (a)-[:MADE]->(b)",
    "MATCH (a:Person {id:'p1'}), (b:Decision {id:'d6'}) MERGE (a)-[:MADE]->(b)",
    "MATCH (a:Person {id:'p2'}), (b:Decision {id:'d1'}) MERGE (a)-[:MADE]->(b)",
    "MATCH (a:Person {id:'p2'}), (b:Decision {id:'d3'}) MERGE (a)-[:MADE]->(b)",
    "MATCH (a:Person {id:'p2'}), (b:Decision {id:'d5'}) MERGE (a)-[:MADE]->(b)",

    # ── Relationships: People → Workflows (OWNS) ─────────────────────────────
    "MATCH (a:Person {id:'p3'}), (b:Workflow {id:'w4'}) MERGE (a)-[:OWNS]->(b)",
    "MATCH (a:Person {id:'p3'}), (b:Workflow {id:'w6'}) MERGE (a)-[:OWNS]->(b)",
    "MATCH (a:Person {id:'p6'}), (b:Workflow {id:'w2'}) MERGE (a)-[:OWNS]->(b)",
    "MATCH (a:Person {id:'p8'}), (b:Workflow {id:'w1'}) MERGE (a)-[:OWNS]->(b)",
    "MATCH (a:Person {id:'p2'}), (b:Workflow {id:'w3'}) MERGE (a)-[:OWNS]->(b)",
    "MATCH (a:Person {id:'p4'}), (b:Workflow {id:'w5'}) MERGE (a)-[:OWNS]->(b)",

    # ── Relationships: Workflows → People (INVOLVES) ──────────────────────────
    "MATCH (a:Workflow {id:'w1'}), (b:Person {id:'p6'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w1'}), (b:Person {id:'p7'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w1'}), (b:Person {id:'p8'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w2'}), (b:Person {id:'p1'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w2'}), (b:Person {id:'p6'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w2'}), (b:Person {id:'p7'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w3'}), (b:Person {id:'p2'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w3'}), (b:Person {id:'p4'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w3'}), (b:Person {id:'p5'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w4'}), (b:Person {id:'p2'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w4'}), (b:Person {id:'p3'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w4'}), (b:Person {id:'p4'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w4'}), (b:Person {id:'p5'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w5'}), (b:Person {id:'p4'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w5'}), (b:Person {id:'p8'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w6'}), (b:Person {id:'p1'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w6'}), (b:Person {id:'p2'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w6'}), (b:Person {id:'p3'}) MERGE (a)-[:INVOLVES]->(b)",
    "MATCH (a:Workflow {id:'w6'}), (b:Person {id:'p6'}) MERGE (a)-[:INVOLVES]->(b)",

    # ── Relationships: Customers → Products (USES) ────────────────────────────
    "MATCH (a:Customer {id:'c1'}), (b:Product {id:'pr1'}) MERGE (a)-[:USES]->(b)",
    "MATCH (a:Customer {id:'c1'}), (b:Product {id:'pr2'}) MERGE (a)-[:USES]->(b)",
    "MATCH (a:Customer {id:'c2'}), (b:Product {id:'pr1'}) MERGE (a)-[:USES]->(b)",
    "MATCH (a:Customer {id:'c2'}), (b:Product {id:'pr3'}) MERGE (a)-[:USES]->(b)",
    "MATCH (a:Customer {id:'c3'}), (b:Product {id:'pr1'}) MERGE (a)-[:USES]->(b)",
    "MATCH (a:Customer {id:'c4'}), (b:Product {id:'pr2'}) MERGE (a)-[:USES]->(b)",
    "MATCH (a:Customer {id:'c5'}), (b:Product {id:'pr1'}) MERGE (a)-[:USES]->(b)",
    "MATCH (a:Customer {id:'c5'}), (b:Product {id:'pr3'}) MERGE (a)-[:USES]->(b)",

    # ── Relationships: Decisions → Products/Customers/Workflows (AFFECTS) ────
    "MATCH (a:Decision {id:'d1'}), (b:Product {id:'pr4'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d2'}), (b:Customer {id:'c3'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d2'}), (b:Workflow {id:'w2'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d3'}), (b:Product {id:'pr1'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d3'}), (b:Product {id:'pr2'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d3'}), (b:Workflow {id:'w4'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d3'}), (b:Workflow {id:'w5'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d4'}), (b:Product {id:'pr2'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d4'}), (b:Workflow {id:'w2'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d5'}), (b:Product {id:'pr1'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d5'}), (b:Product {id:'pr2'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d5'}), (b:Workflow {id:'w5'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d6'}), (b:Product {id:'pr3'}) MERGE (a)-[:AFFECTS]->(b)",
    "MATCH (a:Decision {id:'d6'}), (b:Workflow {id:'w4'}) MERGE (a)-[:AFFECTS]->(b)",

    # ── Relationships: Workflows → Workflows (DEPENDS_ON) ────────────────────
    "MATCH (a:Workflow {id:'w1'}), (b:Workflow {id:'w2'}) MERGE (a)-[:DEPENDS_ON]->(b)",
    "MATCH (a:Workflow {id:'w4'}), (b:Workflow {id:'w3'}) MERGE (a)-[:DEPENDS_ON]->(b)",
    "MATCH (a:Workflow {id:'w5'}), (b:Workflow {id:'w4'}) MERGE (a)-[:DEPENDS_ON]->(b)",
    "MATCH (a:Workflow {id:'w6'}), (b:Workflow {id:'w4'}) MERGE (a)-[:DEPENDS_ON]->(b)",

    # ── Relationships: Workflows → Products (PRODUCES) ────────────────────────
    "MATCH (a:Workflow {id:'w4'}), (b:Product {id:'pr1'}) MERGE (a)-[:PRODUCES]->(b)",
    "MATCH (a:Workflow {id:'w4'}), (b:Product {id:'pr2'}) MERGE (a)-[:PRODUCES]->(b)",
    "MATCH (a:Workflow {id:'w4'}), (b:Product {id:'pr3'}) MERGE (a)-[:PRODUCES]->(b)",
]


def seed():
    print("Setting up constraints...")
    for stmt in CYPHER_SETUP.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                run(stmt)
            except Exception as e:
                print(f"  Constraint (may already exist): {e}")

    print(f"Loading {len(SEED_QUERIES)} seed statements...")
    for i, q in enumerate(SEED_QUERIES):
        run(q)
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(SEED_QUERIES)} done")

    from graph import graph_stats
    stats = graph_stats()
    print("\nGraph seeded successfully!")
    print(f"  Nodes by type: {stats['nodes']}")
    print(f"  Total relationships: {stats['relationships']}")


if __name__ == "__main__":
    seed()
