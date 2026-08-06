# KUP Merge Policy

**Mission:** GAIOS-002 Phase 8.5
**Created:** 2026-08-04
**Status:** Active

---

## Policy

Before creating any new knowledge, search existing knowledge.
If similar knowledge exists, update it instead of creating new.

---

## Search Locations

Before creating knowledge, search:
- Memory (PROJECT_MEMORY.md)
- Skills (.ai/core/skills/)
- Playbooks (.ai/core/playbooks/)
- Runbooks (.ai/core/runbooks/)
- ADR (docs/adr/)
- Lessons (.ai/core/lessons/)
- Failures (.ai/core/failures/)
- Research (.ai/core/research/)
- Registry (.ai/core/registry/)
- Constitution (AI_OPERATING_CONSTITUTION.md)
- Bootstrap (AI_BOOTSTRAP.md)

---

## Merge Rules

### If Similar Knowledge Exists

1. **Update it** — Modify the existing knowledge
2. **Version it** — Increment version number
3. **Cross-reference it** — Add references to related knowledge
4. **Do NOT duplicate it** — Never create a new entry

### If No Similar Knowledge Exists

1. **Create it** — Create new knowledge entry
2. **Version it** — Start at version 1.0.0
3. **Register it** — Add to registry
4. **Cross-reference it** — Add references to related knowledge

---

## Merge Process

1. Search for existing knowledge
2. If found:
   - Read existing knowledge
   - Determine if update is needed
   - Create KUP for update
   - Follow approval workflow
   - Merge changes
   - Update version
3. If not found:
   - Create KUP for new knowledge
   - Follow approval workflow
   - Create knowledge
   - Register in registry
   - Add to knowledge graph

---

## Version Merging

When merging versions:
1. Preserve all historical versions
2. Never overwrite historical knowledge
3. Record change summary
4. Record author and reviewer
5. Record approval date

---

## Conflict Resolution

If conflicts exist between knowledge:
1. Check constitution (highest authority)
2. Check ADRs (architecture decisions)
3. Check most recent approval
4. Escalate to project owner if unresolved

---

## References

- `.ai/core/kup/README.md` — KUP system
- `.ai/core/registry/REGISTRY.md` — Knowledge registry
- `.ai/core/graph/README.md` — Knowledge graph
