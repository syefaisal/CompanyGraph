"""
Seed the knowledge graph with Meridian Property Group — a PropTech SaaS company
providing software for residential and commercial property management.
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
        name: 'Elena Rodriguez', role: 'CEO', department: 'Executive',
        email: 'elena@meridianpg.com', tenure_years: 6
    }""",
    """MERGE (n:Person {id: 'p2'}) SET n += {
        name: 'James Park', role: 'VP Operations', department: 'Operations',
        email: 'james@meridianpg.com', tenure_years: 5
    }""",
    """MERGE (n:Person {id: 'p3'}) SET n += {
        name: 'Sofia Nguyen', role: 'Head of Product', department: 'Product',
        email: 'sofia@meridianpg.com', tenure_years: 3
    }""",
    """MERGE (n:Person {id: 'p4'}) SET n += {
        name: 'Marcus Webb', role: 'Senior Engineer', department: 'Engineering',
        email: 'marcus@meridianpg.com', tenure_years: 4
    }""",
    """MERGE (n:Person {id: 'p5'}) SET n += {
        name: 'Priya Okafor', role: 'Engineer', department: 'Engineering',
        email: 'priya@meridianpg.com', tenure_years: 2
    }""",
    """MERGE (n:Person {id: 'p6'}) SET n += {
        name: 'David Chen', role: 'Director of Compliance', department: 'Compliance',
        email: 'david@meridianpg.com', tenure_years: 4
    }""",
    """MERGE (n:Person {id: 'p7'}) SET n += {
        name: 'Rachel Torres', role: 'Leasing Director', department: 'Leasing',
        email: 'rachel@meridianpg.com', tenure_years: 5
    }""",
    """MERGE (n:Person {id: 'p8'}) SET n += {
        name: 'Andre Williams', role: 'Customer Success Lead', department: 'Customer Success',
        email: 'andre@meridianpg.com', tenure_years: 2
    }""",

    # ── Products ─────────────────────────────────────────────────────────────────
    """MERGE (n:Product {id: 'pr1'}) SET n += {
        name: 'LeaseTrack', category: 'Lease Management', status: 'active',
        version: '3.1', mrr_usd: 95000,
        description: 'Lease lifecycle management and document automation platform'
    }""",
    """MERGE (n:Product {id: 'pr2'}) SET n += {
        name: 'MaintenanceOS', category: 'Work Order Management', status: 'active',
        version: '2.4', mrr_usd: 72000,
        description: 'Work order tracking, vendor coordination, and maintenance reporting'
    }""",
    """MERGE (n:Product {id: 'pr3'}) SET n += {
        name: 'TenantPay', category: 'Payment Processing', status: 'active',
        version: '1.8', mrr_usd: 48000,
        description: 'Rent collection and payment processing portal with ACH and card support'
    }""",
    """MERGE (n:Product {id: 'pr4'}) SET n += {
        name: 'OwnerInsight', category: 'Analytics Dashboard', status: 'beta',
        version: '0.7', mrr_usd: 8000,
        description: 'Property analytics and owner reporting dashboard — occupancy, costs, rental income'
    }""",
    """MERGE (n:Product {id: 'pr5'}) SET n += {
        name: 'LegacyPortal', category: 'Tenant Portal', status: 'deprecated',
        version: '1.2', mrr_usd: 0,
        description: 'Original self-service tenant portal, sunset in favor of TenantPay'
    }""",

    # ── Customers ────────────────────────────────────────────────────────────────
    """MERGE (n:Customer {id: 'c1'}) SET n += {
        name: 'Sunstone Residential', industry: 'Residential Property Management',
        tier: 'enterprise', region: 'Texas', units: 3200, arr_usd: 285000,
        since: '2021-03-15', description: 'Largest enterprise customer, 3200 residential units across Texas'
    }""",
    """MERGE (n:Customer {id: 'c2'}) SET n += {
        name: 'Harbor View Properties', industry: 'Mixed-Use Property Management',
        tier: 'enterprise', region: 'Texas', units: 1800, arr_usd: 210000,
        since: '2022-01-10', description: 'Mixed-use residential and retail manager, Houston and Austin'
    }""",
    """MERGE (n:Customer {id: 'c3'}) SET n += {
        name: 'Metro Living Group', industry: 'Residential Property Management',
        tier: 'mid-market', region: 'Texas', units: 900, arr_usd: 84000,
        since: '2023-07-01', description: 'Mid-market residential manager with 900 units'
    }""",
    """MERGE (n:Customer {id: 'c4'}) SET n += {
        name: 'Summit HOA', industry: 'HOA Management',
        tier: 'smb', region: 'Texas', units: 320, arr_usd: 24000,
        since: '2024-02-20', description: 'HOA management firm covering three suburban communities'
    }""",
    """MERGE (n:Customer {id: 'c5'}) SET n += {
        name: 'Apex Commercial', industry: 'Commercial Property Management',
        tier: 'enterprise', region: 'Gulf Coast', sqft: 2000000, arr_usd: 195000,
        since: '2023-10-01', description: 'Commercial property manager, 2M sqft office and industrial space'
    }""",

    # ── Workflows ────────────────────────────────────────────────────────────────
    """MERGE (n:Workflow {id: 'w1'}) SET n += {
        name: 'Lease Renewal', type: 'customer-facing', status: 'active',
        avg_duration_days: 30,
        description: '90-day tenant renewal covering credit re-check, market rent analysis, negotiation, document generation, and e-signature'
    }""",
    """MERGE (n:Workflow {id: 'w2'}) SET n += {
        name: 'Move-In Inspection', type: 'customer-facing', status: 'active',
        avg_duration_days: 3,
        description: 'Unit condition documentation, key handover, utility transfer, and initial maintenance ticket creation'
    }""",
    """MERGE (n:Workflow {id: 'w3'}) SET n += {
        name: 'Work Order Processing', type: 'operational', status: 'active',
        avg_duration_days: 5,
        description: 'Maintenance request intake, vendor assignment, scheduling, completion verification, invoice reconciliation'
    }""",
    """MERGE (n:Workflow {id: 'w4'}) SET n += {
        name: 'Fair Housing Audit', type: 'compliance', status: 'active',
        avg_duration_days: 14,
        description: 'Quarterly audit of leasing decisions and screening criteria against federal and state fair housing regulations'
    }""",
    """MERGE (n:Workflow {id: 'w5'}) SET n += {
        name: 'Vendor Onboarding', type: 'operational', status: 'active',
        avg_duration_days: 7,
        description: 'License verification, insurance validation, background check, and contract setup for new maintenance vendors'
    }""",
    """MERGE (n:Workflow {id: 'w6'}) SET n += {
        name: 'Quarterly Owner Reporting', type: 'reporting', status: 'active',
        avg_duration_days: 10,
        description: 'Generation and delivery of financial and occupancy performance reports to property owners'
    }""",

    # ── Decisions ────────────────────────────────────────────────────────────────
    """MERGE (n:Decision {id: 'd1'}) SET n += {
        name: 'Deprecate LegacyPortal',
        title: 'Sunset original tenant portal in favor of TenantPay',
        date: '2024-08-01', outcome: 'approved',
        rationale: 'High maintenance cost, low adoption relative to TenantPay; need to consolidate tenant-facing surface area'
    }""",
    """MERGE (n:Decision {id: 'd2'}) SET n += {
        name: 'Enter Commercial Market',
        title: 'Expand platform to serve commercial property managers',
        date: '2023-09-15', outcome: 'approved',
        rationale: 'Strong inbound demand from commercial managers; Apex Commercial agreed to anchor the beta'
    }""",
    """MERGE (n:Decision {id: 'd3'}) SET n += {
        name: 'Migrate to Kubernetes',
        title: 'Move all services from EC2 to Kubernetes for autoscaling',
        date: '2024-02-10', outcome: 'approved',
        rationale: 'Needed for autoscaling to support enterprise SLAs and reduce per-unit cloud cost'
    }""",
    """MERGE (n:Decision {id: 'd4'}) SET n += {
        name: 'GDPR and CCPA Compliance Overhaul',
        title: 'Full audit and remediation of PII handling for data privacy regulations',
        date: '2024-04-05', outcome: 'approved',
        rationale: 'Proactive compliance ahead of regulatory expansion; enterprise customer DPA requirements triggered urgency'
    }""",
    """MERGE (n:Decision {id: 'd5'}) SET n += {
        name: 'Launch OwnerInsight Beta',
        title: 'Ship OwnerInsight analytics product to enterprise customers before GA',
        date: '2025-01-20', outcome: 'approved',
        rationale: 'Strong co-development signal from Sunstone and Harbor View; faster feedback loop than internal testing'
    }""",
    """MERGE (n:Decision {id: 'd6'}) SET n += {
        name: 'Outsource Vendor Network',
        title: 'Transition from in-house vendor directory to curated third-party partner network',
        date: '2024-11-30', outcome: 'approved',
        rationale: 'Reduces operational overhead; partner network improves vendor quality scores and insurance compliance'
    }""",

    # ── People → Products (WORKS_ON) ──────────────────────────────────────────
    "MATCH (a:Person {id:'p4'}), (b:Product {id:'pr1'}) MERGE (a)-[:WORKS_ON]->(b)",  # Marcus → LeaseTrack
    "MATCH (a:Person {id:'p4'}), (b:Product {id:'pr2'}) MERGE (a)-[:WORKS_ON]->(b)",  # Marcus → MaintenanceOS
    "MATCH (a:Person {id:'p5'}), (b:Product {id:'pr3'}) MERGE (a)-[:WORKS_ON]->(b)",  # Priya → TenantPay
    "MATCH (a:Person {id:'p5'}), (b:Product {id:'pr4'}) MERGE (a)-[:WORKS_ON]->(b)",  # Priya → OwnerInsight
    "MATCH (a:Person {id:'p3'}), (b:Product {id:'pr1'}) MERGE (a)-[:WORKS_ON]->(b)",  # Sofia → LeaseTrack
    "MATCH (a:Person {id:'p3'}), (b:Product {id:'pr3'}) MERGE (a)-[:WORKS_ON]->(b)",  # Sofia → TenantPay
    "MATCH (a:Person {id:'p3'}), (b:Product {id:'pr4'}) MERGE (a)-[:WORKS_ON]->(b)",  # Sofia → OwnerInsight
    "MATCH (a:Person {id:'p2'}), (b:Product {id:'pr2'}) MERGE (a)-[:WORKS_ON]->(b)",  # James → MaintenanceOS

    # ── People → Decisions (MADE) ─────────────────────────────────────────────
    "MATCH (a:Person {id:'p1'}), (b:Decision {id:'d2'}) MERGE (a)-[:MADE]->(b)",  # Elena → Enter Commercial
    "MATCH (a:Person {id:'p1'}), (b:Decision {id:'d5'}) MERGE (a)-[:MADE]->(b)",  # Elena → Launch OwnerInsight
    "MATCH (a:Person {id:'p2'}), (b:Decision {id:'d1'}) MERGE (a)-[:MADE]->(b)",  # James → Deprecate LegacyPortal
    "MATCH (a:Person {id:'p2'}), (b:Decision {id:'d3'}) MERGE (a)-[:MADE]->(b)",  # James → K8s Migration
    "MATCH (a:Person {id:'p2'}), (b:Decision {id:'d6'}) MERGE (a)-[:MADE]->(b)",  # James → Outsource Vendor
    "MATCH (a:Person {id:'p6'}), (b:Decision {id:'d4'}) MERGE (a)-[:MADE]->(b)",  # David → GDPR/CCPA

    # ── People → Workflows (OWNS) ─────────────────────────────────────────────
    "MATCH (a:Person {id:'p7'}), (b:Workflow {id:'w1'}) MERGE (a)-[:OWNS]->(b)",  # Rachel → Lease Renewal
    "MATCH (a:Person {id:'p2'}), (b:Workflow {id:'w2'}) MERGE (a)-[:OWNS]->(b)",  # James → Move-In Inspection
    "MATCH (a:Person {id:'p4'}), (b:Workflow {id:'w3'}) MERGE (a)-[:OWNS]->(b)",  # Marcus → Work Order Processing
    "MATCH (a:Person {id:'p6'}), (b:Workflow {id:'w4'}) MERGE (a)-[:OWNS]->(b)",  # David → Fair Housing Audit
    "MATCH (a:Person {id:'p3'}), (b:Workflow {id:'w5'}) MERGE (a)-[:OWNS]->(b)",  # Sofia → Vendor Onboarding
    "MATCH (a:Person {id:'p3'}), (b:Workflow {id:'w6'}) MERGE (a)-[:OWNS]->(b)",  # Sofia → Quarterly Reporting

    # ── Workflows → People (INVOLVES) ────────────────────────────────────────
    "MATCH (a:Workflow {id:'w1'}), (b:Person {id:'p5'}) MERGE (a)-[:INVOLVES]->(b)",  # Lease Renewal → Priya
    "MATCH (a:Workflow {id:'w1'}), (b:Person {id:'p7'}) MERGE (a)-[:INVOLVES]->(b)",  # Lease Renewal → Rachel
    "MATCH (a:Workflow {id:'w1'}), (b:Person {id:'p8'}) MERGE (a)-[:INVOLVES]->(b)",  # Lease Renewal → Andre
    "MATCH (a:Workflow {id:'w2'}), (b:Person {id:'p7'}) MERGE (a)-[:INVOLVES]->(b)",  # Move-In → Rachel
    "MATCH (a:Workflow {id:'w2'}), (b:Person {id:'p4'}) MERGE (a)-[:INVOLVES]->(b)",  # Move-In → Marcus
    "MATCH (a:Workflow {id:'w3'}), (b:Person {id:'p4'}) MERGE (a)-[:INVOLVES]->(b)",  # Work Order → Marcus
    "MATCH (a:Workflow {id:'w3'}), (b:Person {id:'p2'}) MERGE (a)-[:INVOLVES]->(b)",  # Work Order → James
    "MATCH (a:Workflow {id:'w3'}), (b:Person {id:'p8'}) MERGE (a)-[:INVOLVES]->(b)",  # Work Order → Andre
    "MATCH (a:Workflow {id:'w4'}), (b:Person {id:'p6'}) MERGE (a)-[:INVOLVES]->(b)",  # Fair Housing → David
    "MATCH (a:Workflow {id:'w4'}), (b:Person {id:'p7'}) MERGE (a)-[:INVOLVES]->(b)",  # Fair Housing → Rachel
    "MATCH (a:Workflow {id:'w4'}), (b:Person {id:'p1'}) MERGE (a)-[:INVOLVES]->(b)",  # Fair Housing → Elena
    "MATCH (a:Workflow {id:'w5'}), (b:Person {id:'p2'}) MERGE (a)-[:INVOLVES]->(b)",  # Vendor Onboarding → James
    "MATCH (a:Workflow {id:'w5'}), (b:Person {id:'p4'}) MERGE (a)-[:INVOLVES]->(b)",  # Vendor Onboarding → Marcus
    "MATCH (a:Workflow {id:'w6'}), (b:Person {id:'p3'}) MERGE (a)-[:INVOLVES]->(b)",  # Quarterly Report → Sofia
    "MATCH (a:Workflow {id:'w6'}), (b:Person {id:'p8'}) MERGE (a)-[:INVOLVES]->(b)",  # Quarterly Report → Andre
    "MATCH (a:Workflow {id:'w6'}), (b:Person {id:'p1'}) MERGE (a)-[:INVOLVES]->(b)",  # Quarterly Report → Elena

    # ── Customers → Products (USES) ───────────────────────────────────────────
    "MATCH (a:Customer {id:'c1'}), (b:Product {id:'pr1'}) MERGE (a)-[:USES]->(b)",  # Sunstone → LeaseTrack
    "MATCH (a:Customer {id:'c1'}), (b:Product {id:'pr2'}) MERGE (a)-[:USES]->(b)",  # Sunstone → MaintenanceOS
    "MATCH (a:Customer {id:'c1'}), (b:Product {id:'pr3'}) MERGE (a)-[:USES]->(b)",  # Sunstone → TenantPay
    "MATCH (a:Customer {id:'c1'}), (b:Product {id:'pr4'}) MERGE (a)-[:USES]->(b)",  # Sunstone → OwnerInsight (beta)
    "MATCH (a:Customer {id:'c2'}), (b:Product {id:'pr1'}) MERGE (a)-[:USES]->(b)",  # Harbor View → LeaseTrack
    "MATCH (a:Customer {id:'c2'}), (b:Product {id:'pr3'}) MERGE (a)-[:USES]->(b)",  # Harbor View → TenantPay
    "MATCH (a:Customer {id:'c2'}), (b:Product {id:'pr4'}) MERGE (a)-[:USES]->(b)",  # Harbor View → OwnerInsight (beta)
    "MATCH (a:Customer {id:'c3'}), (b:Product {id:'pr1'}) MERGE (a)-[:USES]->(b)",  # Metro Living → LeaseTrack
    "MATCH (a:Customer {id:'c3'}), (b:Product {id:'pr2'}) MERGE (a)-[:USES]->(b)",  # Metro Living → MaintenanceOS
    "MATCH (a:Customer {id:'c4'}), (b:Product {id:'pr1'}) MERGE (a)-[:USES]->(b)",  # Summit HOA → LeaseTrack
    "MATCH (a:Customer {id:'c4'}), (b:Product {id:'pr3'}) MERGE (a)-[:USES]->(b)",  # Summit HOA → TenantPay
    "MATCH (a:Customer {id:'c5'}), (b:Product {id:'pr2'}) MERGE (a)-[:USES]->(b)",  # Apex → MaintenanceOS
    "MATCH (a:Customer {id:'c5'}), (b:Product {id:'pr4'}) MERGE (a)-[:USES]->(b)",  # Apex → OwnerInsight (beta)

    # ── Decisions → Entities (AFFECTS) ───────────────────────────────────────
    "MATCH (a:Decision {id:'d1'}), (b:Product {id:'pr5'}) MERGE (a)-[:AFFECTS]->(b)",   # Deprecate → LegacyPortal
    "MATCH (a:Decision {id:'d2'}), (b:Customer {id:'c5'}) MERGE (a)-[:AFFECTS]->(b)",   # Commercial → Apex
    "MATCH (a:Decision {id:'d2'}), (b:Workflow {id:'w6'}) MERGE (a)-[:AFFECTS]->(b)",   # Commercial → Quarterly Reporting
    "MATCH (a:Decision {id:'d3'}), (b:Product {id:'pr1'}) MERGE (a)-[:AFFECTS]->(b)",   # K8s → LeaseTrack
    "MATCH (a:Decision {id:'d3'}), (b:Product {id:'pr2'}) MERGE (a)-[:AFFECTS]->(b)",   # K8s → MaintenanceOS
    "MATCH (a:Decision {id:'d3'}), (b:Product {id:'pr3'}) MERGE (a)-[:AFFECTS]->(b)",   # K8s → TenantPay
    "MATCH (a:Decision {id:'d3'}), (b:Workflow {id:'w3'}) MERGE (a)-[:AFFECTS]->(b)",   # K8s → Work Order Processing
    "MATCH (a:Decision {id:'d4'}), (b:Product {id:'pr1'}) MERGE (a)-[:AFFECTS]->(b)",   # GDPR/CCPA → LeaseTrack
    "MATCH (a:Decision {id:'d4'}), (b:Product {id:'pr3'}) MERGE (a)-[:AFFECTS]->(b)",   # GDPR/CCPA → TenantPay
    "MATCH (a:Decision {id:'d4'}), (b:Workflow {id:'w1'}) MERGE (a)-[:AFFECTS]->(b)",   # GDPR/CCPA → Lease Renewal
    "MATCH (a:Decision {id:'d5'}), (b:Product {id:'pr4'}) MERGE (a)-[:AFFECTS]->(b)",   # OwnerInsight Beta → product
    "MATCH (a:Decision {id:'d5'}), (b:Customer {id:'c1'}) MERGE (a)-[:AFFECTS]->(b)",   # OwnerInsight Beta → Sunstone
    "MATCH (a:Decision {id:'d5'}), (b:Customer {id:'c2'}) MERGE (a)-[:AFFECTS]->(b)",   # OwnerInsight Beta → Harbor View
    "MATCH (a:Decision {id:'d6'}), (b:Workflow {id:'w3'}) MERGE (a)-[:AFFECTS]->(b)",   # Outsource Vendor → Work Order
    "MATCH (a:Decision {id:'d6'}), (b:Workflow {id:'w5'}) MERGE (a)-[:AFFECTS]->(b)",   # Outsource Vendor → Vendor Onboarding

    # ── Workflows → Workflows (DEPENDS_ON) ───────────────────────────────────
    "MATCH (a:Workflow {id:'w1'}), (b:Workflow {id:'w4'}) MERGE (a)-[:DEPENDS_ON]->(b)",  # Lease Renewal → Fair Housing Audit
    "MATCH (a:Workflow {id:'w2'}), (b:Workflow {id:'w1'}) MERGE (a)-[:DEPENDS_ON]->(b)",  # Move-In → Lease Renewal
    "MATCH (a:Workflow {id:'w3'}), (b:Workflow {id:'w5'}) MERGE (a)-[:DEPENDS_ON]->(b)",  # Work Order → Vendor Onboarding
    "MATCH (a:Workflow {id:'w6'}), (b:Workflow {id:'w3'}) MERGE (a)-[:DEPENDS_ON]->(b)",  # Quarterly Report → Work Order

    # ── Workflows → Products (PRODUCES) ──────────────────────────────────────
    "MATCH (a:Workflow {id:'w1'}), (b:Product {id:'pr1'}) MERGE (a)-[:PRODUCES]->(b)",  # Lease Renewal → LeaseTrack
    "MATCH (a:Workflow {id:'w3'}), (b:Product {id:'pr2'}) MERGE (a)-[:PRODUCES]->(b)",  # Work Order → MaintenanceOS
    "MATCH (a:Workflow {id:'w6'}), (b:Product {id:'pr4'}) MERGE (a)-[:PRODUCES]->(b)",  # Quarterly Report → OwnerInsight
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

    print("Clearing existing data...")
    run("MATCH (n) DETACH DELETE n")

    print(f"Loading {len(SEED_QUERIES)} seed statements...")
    for i, q in enumerate(SEED_QUERIES):
        run(q)
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(SEED_QUERIES)} done")

    from graph import graph_stats
    stats = graph_stats()
    print("\nGraph seeded — Meridian Property Group")
    print(f"  Nodes by type: {stats['nodes']}")
    print(f"  Total relationships: {stats['relationships']}")


if __name__ == "__main__":
    seed()
