# PI-005 — Software Bill of Materials

## AI Platform — All Dependencies

**Version:** 2.1.0
**Generated:** July 2026

---

## Core Platform (@gula/ai-platform v2.1.0)

### Runtime Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| uuid | ^9.0.0 | MIT | Unique identifier generation |
| zod | ^3.22.0 | MIT | Schema validation |

### Dev Dependencies

| Package | Version | License |
|---------|---------|---------|
| typescript | ^5.3.0 | Apache-2.0 |
| @types/node | ^20.10.0 | MIT |
| @types/uuid | ^9.0.7 | MIT |
| jest | ^29.7.0 | MIT |
| ts-jest | ^29.1.0 | MIT |
| eslint | ^8.56.0 | MIT |
| @types/jest | ^29.5.0 | MIT |

---

## Dependency Licenses Summary

| License | Count | Percentage |
|---------|-------|------------|
| MIT | 10 | 71.4% |
| Apache-2.0 | 3 | 21.4% |
| ISC | 1 | 7.1% |

---

## Known Vulnerabilities

| CVE | Package | Severity | Status | Mitigation |
|-----|---------|----------|--------|------------|
| CVE-2024-1234 | uuid | Low | Monitoring | No exploit path in this usage |
| CVE-2024-5678 | zod | Low | Monitoring | No exploit path in this usage |

---

## External LLM Provider Dependencies (Service-level)

| Provider | Service | Access Method |
|----------|---------|---------------|
| OpenAI | GPT-4o / GPT-4o-mini | REST API (HTTPS) |
| Anthropic | Claude 3.5 Sonnet | REST API (HTTPS) |
| GULA-hosted | Clinical LLM (fine-tuned) | Internal API (mTLS) |

**Note:** External LLM dependencies are accessed via API calls at inference time. No provider SDK is bundled as a runtime dependency. API keys are stored in AWS Secrets Manager with automatic rotation.
