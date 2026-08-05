# BUILDER_AUDIT_REPORT.md

Repository audit for the GULA Builder Engine (GULA-BUILDER-001).

## Discovery

| Category | Count | Detail |
|---|---|---|
| backend | 20899 | 20899 files under backend/ |
| frontend | 136 | 136 files under frontend-v3/src |
| knowledge-system | 113 | 113 files across 52 directories |
| infrastructure | 465 | 465 files across 6 surfaces |
| ai-systems | 155 | 155 files across 6 systems |
| documentation | 609 | 609 files under docs/ |
| dependencies | 6 | 6 manifests located |
| services | 10 | 10 service directories under services/ |

## Detailed Entries

### backend

- __pycache__
- ai
- ai_fabric
- approvals
- audit
- biomedical
- blood_bank
- capabilities
- care_continuum
- certification
- citizen_platform
- clinical

### frontend

- api
- assets
- components
- constants
- contexts
- hooks
- i18n
- layouts
- lib
- pages
- permissions
- routes

### knowledge-system

- api
- architecture
- automation
- backend
- builder
- capabilities
- checklists
- checkpoints
- compat
- constitution
- database
- decisions
- deployment
- desktop
- devops
- events
- evolution
- failures
- frontend
- governor
- graph
- health
- incidents
- index
- infrastructure
- kernel
- kup
- lessons
- marketplace
- memory
- migrations
- mobile
- monitoring
- observability
- performance
- playbooks
- policies
- prompts
- quality
- registry
- reports
- research
- reviews
- roadmap
- runbooks
- sdk
- security
- skills
- templates
- testing
- traceability
- workflows

### infrastructure

- docker (2)
- k8s (43)
- helm (38)
- terraform (68)
- ci (26)
- deploy-scripts (288)

### ai-systems

- kernel (68 files)
- ext (24 files)
- builder (24 files)
- governor (34 files)
- validation (3 files)
- brain (2 files)

### documentation

- adr
- ai
- api
- architecture
- audit
- bootstrap
- brain
- builder
- catalog
- certification
- checklists
- configuration
- constitution
- database
- decisions
- deployment
- development
- discovery
- domain
- dr
- ecosystem
- engineering
- enterprise
- enterprise-readiness
- environment
- events
- evolution
- execution
- factory
- foundation
- freeze
- frontend
- genome
- governance
- governor
- healthcare
- hospital-workspace
- kernel
- learning
- management
- metrics
- national
- niam
- nursing-platform
- operations
- ops
- performance
- pharmacy-platform
- platform
- playbooks
- policies
- preview
- production
- quality
- radiology-platform
- reference
- release
- releases
- reports
- roadmaps
- runbooks
- runtime
- sbom
- security
- sndhs
- sovereign
- standards
- technical-debt
- templates
- trust
- ux-audit
- workflows

### dependencies

- pyproject.toml (119 lines)
- requirements.txt (4 lines)
- backend/pyproject.toml (51 lines)
- shared/pyproject.toml (59 lines)
- package.json (94 lines)
- frontend-v3/package.json (50 lines)

### services

- ai
- autonomous_manager
- device_bridge
- lab
- notification
- order
- patient
- result
- sample
- shared

## Findings

- [low] BA-4 — AI systems present: 155 files across existing engines
- [low] BA-5 — Documentation present: 609 files under docs/
- [medium] BA-7 — Builder Engine absent: scripts/builder not yet registered in ai-systems

## Verdict

**AUDIT COMPLETE** — 3 findings, none high/critical.
