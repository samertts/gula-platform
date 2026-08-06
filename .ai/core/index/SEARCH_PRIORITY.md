# Search Priority

**Mission:** GAIOS-MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Defines task-type-specific search strategies. Every AI decision must
search the right knowledge in the right order before investigating
externally.

---

## Universal Search Order

1. Constitution (AI_OPERATING_CONSTITUTION.md)
2. Bootstrap (AI_BOOTSTRAP.md)
3. ADR (docs/adr/)
4. Architecture (docs/architecture/)
5. Memory (.ai/core/memory/)
6. Skills (.ai/core/skills/)
7. Playbooks (.ai/core/playbooks/)
8. Runbooks (.ai/core/runbooks/)
9. Registry (.ai/core/registry/)
10. Documentation (docs/)
11. Git History
12. External Sources

---

## Task-Type Search Strategies

### Bug Fix
1. Failures (.ai/core/failures/)
2. Lessons (.ai/core/lessons/)
3. Skills (.ai/core/skills/)
4. Git History (blame, log)
5. Existing Code
6. External (only if stuck)

### Feature Implementation
1. Capabilities (.ai/core/capabilities/)
2. Decisions (.ai/core/decisions/)
3. ADR (docs/adr/)
4. Architecture (docs/architecture/)
5. Skills (.ai/core/skills/)
6. Existing Code
7. External (only if stuck)

### Refactoring
1. Architecture (docs/architecture/)
2. ADR (docs/adr/)
3. Decisions (.ai/core/decisions/)
4. Capabilities (.ai/core/capabilities/)
5. Existing Code
6. External (only if stuck)

### Incident Response
1. Runbooks (.ai/core/runbooks/)
2. Incidents (.ai/core/incidents/)
3. Failures (.ai/core/failures/)
4. Lessons (.ai/core/lessons/)
5. Existing Code
6. External (only if stuck)

### Security Issue
1. Constitution (security section)
2. Security docs (docs/security/)
3. ADR (security-related)
4. Failures (.ai/core/failures/)
5. Existing Code
6. External (OWASP, CWE)

### Performance Issue
1. Performance docs (.ai/core/performance/)
2. ADR (performance-related)
3. Failures (.ai/core/failures/)
4. Existing Code
5. External (only if stuck)

### Knowledge Update
1. Memory (.ai/core/memory/)
2. Skills (.ai/core/skills/)
3. Playbooks (.ai/core/playbooks/)
4. Runbooks (.ai/core/runbooks/)
5. Registry (.ai/core/registry/)
6. KUP (.ai/core/kup/)
7. External (only if stuck)

### Deployment
1. Runbooks (.ai/core/runbooks/)
2. Playbooks (.ai/core/playbooks/)
3. Deployment docs (.ai/core/deployment/)
4. DevOps docs (.ai/core/devops/)
5. External (only if stuck)

---

## Search Rules

1. **Never skip search** — Always search before implementing
2. **Never assume** — Verify knowledge exists
3. **Never duplicate** — Check if similar knowledge exists
4. **Always cross-reference** — Follow related knowledge links
5. **Always verify freshness** — Check last updated date
6. **Always document** — Record what was found

---

## Fallback Chain

If primary search fails:

1. Try related knowledge (cross-references)
2. Try git history (previous attempts)
3. Try existing code (patterns)
4. Try external sources (documentation)
5. Try AI inference (last resort)

---

## References

- `.ai/core/index/SEARCH_INDEX.md` — Search indexes
- `.ai/core/index/INDEX.md` — Master index
- `.ai/README.md` — Execution policy
