# GULA Platform Roadmap 2035

## Vision for 2035

By 2035, GULA shall be:
- The unified national healthcare platform of Iraq
- Interoperable with every major healthcare system in the region
- Recognized as one of the world's most advanced sovereign healthcare platforms
- A platform that enables world-class health outcomes for the Iraqi people

## Strategic Horizons

### Horizon 1: Foundation (2025-2027)
*Current phase — establishing the core platform*

| Milestone | Target | Status |
|-----------|--------|--------|
| Laboratory platform complete | Q1 2026 | In progress |
| V5 Enterprise Certification | Q2 2026 | Achieved (94/100) |
| RC-1 Release | Q3 2026 | Achieved |
| Authorization & Identity Expansion | Q3 2026 | In progress |
| Clinical workflow integration | Q4 2026 | Planned |
| National identity integration | Q1 2027 | Planned |
| FHIR R4B compliance | Q2 2027 | Planned |

### Horizon 2: National Platform (2027-2029)
*Scaling from laboratory to national healthcare platform*

| Milestone | Target |
|-----------|--------|
| Multi-tenant nation-wide deployment | 2027 |
| ePrescription exchange | 2027 |
| National EHR (core) | 2028 |
| Public health surveillance | 2028 |
| Immunization registry | 2028 |
| National analytics dashboard for MoH | 2028 |
| Referral network | 2029 |
| Citizen portal with PHR access | 2029 |
| AI copilot (clinical decision support) | 2029 |

### Horizon 3: Intelligent Platform (2029-2032)
*AI-native capabilities at national scale*

| Milestone | Target |
|-----------|--------|
| Predictive population health | 2030 |
| Disease outbreak prediction | 2030 |
| AI-assisted diagnosis (radiology, pathology) | 2031 |
| Automated clinical coding | 2031 |
| National cancer registry | 2031 |
| Research data lake | 2032 |
| Genomic data integration | 2032 |
| Personalized medicine support | 2032 |

### Horizon 4: Regional & Global (2032-2035)
*Extending beyond national borders*

| Milestone | Target |
|-----------|--------|
| Arab Health interoperability | 2033 |
| WHO SMART guideline compliance | 2033 |
| Regional health data exchange | 2034 |
| Global health research contribution | 2034 |
| International certification (HIMSS, ONC) | 2035 |
| Next-generation platform architecture | 2035 |

## Architecture Evolution

### 2025-2027 (Current)
- FastAPI monolith (`backend/app/`)
- PostgreSQL 16 + Redis 7
- React + Firebase frontend (`frontend-v2/`)
- Device bridge for lab instruments (`services/device_bridge/`)
- Modular monolith architecture

### 2027-2029
- Domain-oriented decomposition
- Event-driven architecture maturity
- FHIR-native APIs
- National identity federation
- Horizontal scaling with read replicas
- Kubernetes deployment (optional)

### 2029-2032
- AI inference platform
- Real-time analytics pipeline
- Advanced cache and search infrastructure
- Multi-region active-active deployment

### 2032-2035
- Anticipated technology evolution
- Quantum-safe cryptography upgrade
- Ambient computing interfaces
- Autonomous health operations

## Guiding Principles for the Roadmap

1. **No rewrite.** Each horizon extends the previous one. The platform evolves; it is never replaced.

2. **Backward compatibility.** Every horizon maintains compatibility with APIs and data from previous horizons.

3. **Continuous deployment.** The platform is always deployable. Horizons are not big-bang releases.

4. **Clinical safety.** No horizon introduces features that compromise clinical safety.

5. **Data sovereignty.** Every horizon strengthens data sovereignty and patient privacy.

6. **Simplicity.** Every horizon resists the temptation to add complexity without proportional value.

## Risk Management

| Risk | Mitigation |
|------|------------|
| Technology obsolescence | Use stable, widely-adopted technologies; avoid vendor lock-in |
| Funding changes | Modular architecture allows incremental investment |
| Team turnover | Constitution, ADRs, documentation ensure continuity |
| Regulatory changes | Standards-based architecture adapts to regulation |
| Security threats | Zero-trust architecture, continuous security improvement |
| Clinical adoption | Clinician involvement in design, continuous feedback |

## Measuring Progress

- **Clinical:** Reduction in turnaround time, improvement in result accuracy, clinician satisfaction scores
- **Technical:** System uptime, API response times, test coverage, security posture
- **National:** Facilities connected, patients registered, results processed, public health reports generated
- **Adoption:** Active users, daily transactions, integration partners, citizen portal engagement

This roadmap is a living document. It is reviewed and updated annually by the Architecture Board.
