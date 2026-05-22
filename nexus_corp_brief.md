# Nexus Corp — Company Overview Brief
*Internal document · Last updated Q1 2025*

---

## Company Overview

Nexus Corp is a B2B SaaS company building data integration and analytics infrastructure for mid-market and enterprise customers. Founded six years ago by Sarah Chen, who serves as CEO, the company has grown to a team of eight core staff across engineering, product, sales, marketing, and customer success.

The CTO is Marcus Rivera, a five-year veteran of the company who leads the engineering organization and oversees all product development. He reports directly to Sarah and owns the technical roadmap.

---

## Team

**Sarah Chen** (CEO, Executive, 6 years) is the company's founder and primary decision-maker on strategic direction. Her email is sarah@nexuscorp.io. She has led the company's healthcare market entry, the DataVault partnership, and the introduction of the freemium tier on the API Platform.

**Marcus Rivera** (CTO, Engineering, 5 years, marcus@nexuscorp.io) oversees all engineering and makes technical decisions. He decided to deprecate the Nexus Mobile product line and to migrate the infrastructure from EC2 to Kubernetes. He also led the GDPR compliance overhaul.

**Priya Patel** (VP Product, Product, 3 years, priya@nexuscorp.io) owns the product roadmap. She works across Nexus Analytics, the Nexus API Platform, and Nexus Connect. She owns the Feature Release workflow and co-owns the Quarterly Planning cycle.

**Alex Kim** (Senior Engineer, Engineering, 4 years, alex@nexuscorp.io) is a senior engineer who contributes to Nexus Analytics and the Nexus API Platform. He owns the Data Migration workflow and is involved in both Bug Triage and Feature Release.

**Jordan Lee** (Engineer, Engineering, 2 years, jordan@nexuscorp.io) works on the Nexus API Platform and Nexus Connect. Jordan participates in Bug Triage and Feature Release workflows.

**Diana Santos** (Head of Sales, Sales, 4 years, diana@nexuscorp.io) owns the Sales Pipeline and is involved in both the Customer Onboarding and Sales Pipeline workflows.

**Tom Mitchell** (Marketing Lead, Marketing, 3 years, tom@nexuscorp.io) supports the Customer Onboarding workflow alongside sales and customer success.

**Aisha Okafor** (Customer Success Manager, Customer Success, 2 years, aisha@nexuscorp.io) owns the Customer Onboarding workflow and is involved in Data Migration support.

---

## Products

**Nexus Analytics** is the company's flagship BI dashboard product (category: BI Dashboard), currently active at version 4.2, generating $180,000 MRR. It is worked on by Marcus Rivera, Priya Patel, and Alex Kim. The Feature Release workflow produces Nexus Analytics.

**Nexus API Platform** is an API gateway product (category: API Gateway), active at version 2.8, generating $95,000 MRR. Contributors include Marcus Rivera, Priya Patel, Alex Kim, and Jordan Lee. Feature Release produces this product as well.

**Nexus Connect** is a data connector product (category: Data Connector) currently in beta at version 0.9, generating $12,000 MRR. Priya Patel and Jordan Lee are working on it. Feature Release also produces Nexus Connect.

**Nexus Mobile** is a deprecated mobile app (category: Mobile App, version 1.5, $0 MRR). It was the target of the Deprecate Nexus Mobile decision and is no longer actively maintained.

---

## Customers

**TechFlow Inc** is an enterprise-tier technology company in North America, generating $240,000 ARR. They have been a customer since 2021-03-15 and use both Nexus Analytics and the Nexus API Platform.

**RetailPro Corp** is an enterprise-tier retail company in North America with $180,000 ARR since 2022-01-10. They use Nexus Analytics and Nexus Connect.

**HealthFirst** is a mid-market healthcare company in North America with $72,000 ARR since 2023-07-01. They use Nexus Analytics and were brought in through the healthcare market expansion. The Enter Healthcare Market decision directly affects them.

**StartupX** is an SMB fintech company based in Europe with $18,000 ARR since 2024-02-20. They use the Nexus API Platform.

**GlobalShip Ltd** is an enterprise-tier logistics company in APAC with $210,000 ARR since 2022-09-05. They use Nexus Analytics and Nexus Connect.

---

## Workflows

**Customer Onboarding** (customer-facing, active, avg 14 days) is the end-to-end process for activating new customers. It is owned by Aisha Okafor and involves Diana Santos and Tom Mitchell. It depends on the Sales Pipeline workflow.

**Sales Pipeline** (revenue, active, avg 45 days) covers lead qualification through contract close. Diana Santos owns it and Sarah Chen is involved, along with Tom Mitchell and Diana herself.

**Bug Triage** (engineering, active, avg 3 days) handles incoming bug classification, assignment, and resolution. Marcus Rivera owns it; Alex Kim and Jordan Lee are involved.

**Feature Release** (engineering, active, avg 21 days) covers the design → build → QA → ship cycle. Priya Patel owns it; Marcus Rivera, Alex Kim, and Jordan Lee are involved. It depends on Bug Triage. Feature Release produces Nexus Analytics, the Nexus API Platform, and Nexus Connect.

**Data Migration** (engineering, active, avg 7 days) handles moving customer data between environments. Alex Kim owns it; Aisha Okafor is involved. It depends on the Feature Release workflow.

**Quarterly Planning** (strategic, active, avg 10 days) covers OKR setting, roadmap prioritization, and resource allocation. Priya Patel owns it; Sarah Chen, Marcus Rivera, and Diana Santos are involved. It depends on Feature Release.

---

## Key Decisions

**Deprecate Nexus Mobile** (d1, approved 2024-09-01) — Marcus Rivera made this decision to sunset the mobile app product line. Rationale: low adoption and high maintenance cost; resources were redirected to the API platform. This decision affects the Nexus Mobile product.

**Enter Healthcare Market** (d2, approved 2023-06-15) — Sarah Chen made this decision to expand the sales motion into the healthcare vertical. Rationale: strong pipeline signal; the HealthFirst pilot exceeded targets. This decision affects HealthFirst (customer) and the Sales Pipeline workflow.

**Migrate to Kubernetes** (d3, approved 2024-01-10) — Marcus Rivera made this decision to move all services from EC2 to Kubernetes. Rationale: needed for autoscaling to support enterprise SLAs. Affects Nexus Analytics, the Nexus API Platform, the Feature Release workflow, and the Data Migration workflow.

**Introduce Freemium Tier** (d4, approved 2024-11-20) — Sarah Chen made this decision to add a free tier to the API Platform as a PLG strategy. Affects the Nexus API Platform and the Sales Pipeline workflow.

**GDPR Compliance Overhaul** (d5, approved 2024-03-05) — Marcus Rivera made this decision following a full audit and remediation of data handling for EU compliance. Triggered by EU customer expansion. Affects Nexus Analytics, the Nexus API Platform, and the Data Migration workflow.

**Partner with DataVault** (d6, approved 2025-01-12) — Sarah Chen made this decision to sign a strategic data-sharing partnership with DataVault, expanding Nexus Connect data sources by 3x without an in-house build. Affects the Nexus Connect product and the Feature Release workflow.
