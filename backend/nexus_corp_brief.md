# Meridian Property Group — Company Brief

Meridian Property Group is a regional PropTech SaaS company headquartered in Austin, Texas. We build software for residential and commercial property management firms, helping them automate leasing, maintenance, payments, compliance, and owner reporting. Our platform currently serves 8,500 residential units and 2 million square feet of commercial space across the Gulf Coast and Southwest.

---

## Our Team

**Elena Rodriguez** is our CEO. She joined six years ago from a real estate investment background and has driven Meridian's expansion into commercial property management. Elena made the strategic decision to enter the commercial market in 2023 and approved the launch of our OwnerInsight analytics product in 2025.

**James Park** is VP Operations with five years at Meridian. He oversees maintenance operations and vendor management, and owns the Move-In Inspection and Work Order Processing workflows. James made the call to deprecate our legacy portal in 2024, led the Kubernetes migration, and decided to outsource our vendor network to a curated partner ecosystem.

**Sofia Nguyen** is Head of Product with three years at Meridian. She drives the roadmap for LeaseTrack, TenantPay, and OwnerInsight, and owns the Vendor Onboarding and Quarterly Owner Reporting workflows.

**Marcus Webb** is a Senior Engineer with four years at the company. He built and maintains LeaseTrack and MaintenanceOS, and owns the Work Order Processing workflow end-to-end. Marcus is the primary engineering contact for our two largest enterprise customers.

**Priya Okafor** is an Engineer with two years at Meridian. She works on TenantPay and OwnerInsight and plays a key role in the Lease Renewal workflow for payment integrations.

**David Chen** is Director of Compliance with four years at Meridian. He owns the Fair Housing Audit workflow and was the driving force behind our GDPR and CCPA compliance overhaul in 2024. David co-authored the PII encryption standards now enforced across all products.

**Rachel Torres** is Leasing Director with five years at Meridian. She owns the Lease Renewal workflow and is deeply involved in Move-In Inspections and Fair Housing Audits.

**Andre Williams** is our Customer Success Lead with two years at Meridian. He is involved in Lease Renewal, Work Order Processing, and Quarterly Owner Reporting, and serves as the primary point of contact for our mid-market and SMB customers.

---

## Our Products

**LeaseTrack** (v3.1, active) is our flagship lease lifecycle management platform. It automates lease drafting, document signing, credit checks, and renewal reminders. Monthly recurring revenue is $95,000. Marcus Webb and Sofia Nguyen lead product and engineering for LeaseTrack.

**MaintenanceOS** (v2.4, active) is our work order and vendor coordination platform. Property managers use it to create maintenance requests, assign vendors, track completion, and generate compliance reports. MRR is $72,000. Marcus Webb leads engineering; James Park oversees operations.

**TenantPay** (v1.8, active) is our rent collection and payment processing portal. It supports ACH, card, and digital wallet payments with automated late fees and receipts. MRR is $48,000. Priya Okafor and Sofia Nguyen lead development.

**OwnerInsight** (v0.7, beta) is our property analytics and owner reporting dashboard. It aggregates occupancy, maintenance costs, and rental income data into real-time dashboards for property owners. MRR is $8,000. Priya Okafor leads engineering. This product is in active beta with our two largest enterprise customers.

**LegacyPortal** (v1.2, deprecated) was our original self-service tenant portal launched in 2019. It was sunset in August 2024 in favor of TenantPay's richer payment and communication features. MRR is $0.

---

## Our Customers

**Sunstone Residential** is our largest customer — an enterprise-tier residential property management firm with 3,200 units across Texas. They use LeaseTrack, MaintenanceOS, TenantPay, and OwnerInsight (beta). Annual recurring revenue is $285,000.

**Harbor View Properties** manages 1,800 mixed-use units across Houston and Austin. They are an enterprise customer using LeaseTrack, TenantPay, and OwnerInsight (beta). ARR is $210,000.

**Metro Living Group** is a mid-market residential manager with 900 units. They use LeaseTrack and MaintenanceOS. ARR is $84,000.

**Summit HOA** manages 320 HOA-governed units across three suburban communities. They are an SMB-tier customer using LeaseTrack and TenantPay. ARR is $24,000.

**Apex Commercial** is our largest commercial customer. They manage 2 million square feet of office and industrial space across the Gulf Coast. Apex uses MaintenanceOS and OwnerInsight and was the anchor customer for our commercial market expansion. ARR is $195,000.

---

## Our Workflows

**Lease Renewal** is a 30-day customer-facing workflow covering credit re-check, market rent analysis, negotiation, updated document generation, and e-signature. Rachel Torres owns this workflow. Priya Okafor handles payment integration, Andre Williams handles customer communication. This workflow depends on the Fair Housing Audit being current.

**Move-In Inspection** is a 3-day workflow covering unit condition photography, key handover, utility transfer, and initial maintenance ticket creation. James Park owns it; Rachel Torres is involved. It depends on Lease Renewal completing first.

**Work Order Processing** is a 5-day operational workflow covering maintenance request intake, vendor assignment, scheduling, work completion verification, and invoice reconciliation. Marcus Webb owns it. James Park and Andre Williams are also involved. This workflow depends on Vendor Onboarding being complete for any new vendor.

**Fair Housing Audit** is a 14-day compliance workflow triggered quarterly. It audits leasing decisions, advertising copy, and applicant screening criteria against federal and state fair housing regulations. David Chen owns it; Rachel Torres and Elena Rodriguez are involved.

**Vendor Onboarding** is a 7-day workflow for screening new maintenance vendors: license verification, insurance validation, background check, and contract setup. Sofia Nguyen owns it; James Park and Marcus Webb are involved.

**Quarterly Owner Reporting** is a 10-day workflow generating and delivering financial and occupancy performance reports to property owners. Sofia Nguyen owns it; Andre Williams and Elena Rodriguez are involved. It depends on Work Order Processing completing on time to include accurate maintenance cost data.

---

## Strategic Decisions

**Deprecate LegacyPortal** (approved 2024-08-01): James Park approved sunsetting our original tenant portal. The rationale was high maintenance cost, low adoption relative to TenantPay, and the need to consolidate our tenant-facing surface area. This directly affected the LegacyPortal product.

**Enter Commercial Market** (approved 2023-09-15): Elena Rodriguez approved expanding Meridian's platform to serve commercial property managers. The rationale was strong inbound demand and Apex Commercial's willingness to anchor the commercial beta. This decision affected Apex Commercial as a customer and added new requirements to Quarterly Owner Reporting.

**Migrate Infrastructure to Kubernetes** (approved 2024-02-10): James Park approved migrating all services from EC2 to Kubernetes for autoscaling, better SLA enforcement, and reduced per-unit cloud cost. This decision affected LeaseTrack, MaintenanceOS, TenantPay, and the Work Order Processing workflow during the migration period.

**GDPR and CCPA Compliance Overhaul** (approved 2024-04-05): David Chen drove and Elena Rodriguez approved a full audit and remediation of all PII handling across the platform. Rationale was proactive compliance ahead of anticipated regulatory expansion and a large enterprise customer's data processing agreement requirements. This affected LeaseTrack, TenantPay, and the Lease Renewal workflow.

**Launch OwnerInsight Beta** (approved 2025-01-20): Elena Rodriguez approved shipping OwnerInsight to enterprise customers before GA. Rationale was strong demand signal from Sunstone Residential and Harbor View, and a desire to co-develop with high-value customers. This decision directly affected the OwnerInsight product and enrolled Sunstone Residential and Harbor View Properties in the beta.

**Outsource Vendor Network** (approved 2024-11-30): James Park approved transitioning from an in-house vendor directory to a curated partner vendor network managed by a third-party platform. Rationale was reducing operational overhead and improving vendor quality scores. This affected the Work Order Processing and Vendor Onboarding workflows.
