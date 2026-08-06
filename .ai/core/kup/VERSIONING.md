# KUP Versioning System

**Mission:** GAIOS-002 Phase 8.5
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Every knowledge object maintains version history.
Knowledge changes must always preserve history.
Never overwrite historical knowledge.

---

## Version Format

```
MAJOR.MINOR.PATCH
```

| Component | When to Increment |
|---|---|
| MAJOR | Breaking change, fundamental rewrite |
| MINOR | New feature, significant addition |
| PATCH | Bug fix, minor correction |

---

## Version Metadata

Every knowledge object includes:

```yaml
version: "1.0.0"
previous_version: "0.9.0"
change_summary: "Initial release"
author: "GAIOS"
reviewer: "Project Owner"
approval_date: "2026-08-04"
constitution_version: "1.0.0"
```

---

## Version History Format

```markdown
## Version History

| Version | Date | Author | Reviewer | Change |
|---|---|---|---|---|
| 1.0.0 | 2026-08-04 | GAIOS | Owner | Initial release |
| 1.1.0 | 2026-08-05 | GAIOS | Owner | Added new feature |
| 1.1.1 | 2026-08-06 | GAIOS | Owner | Fixed bug |
```

---

## Rules

1. **Never overwrite** — Always preserve historical versions
2. **Always increment** — Version must change on every modification
3. **Always document** — Record what changed and why
4. **Always record** — Author, reviewer, approval date
5. **Always reference** — Constitution version at time of change

---

## Version Examples

### Initial Creation
```yaml
version: "1.0.0"
previous_version: null
change_summary: "Initial creation"
```

### Minor Update
```yaml
version: "1.1.0"
previous_version: "1.0.0"
change_summary: "Added new capability"
```

### Major Rewrite
```yaml
version: "2.0.0"
previous_version: "1.5.0"
change_summary: "Complete rewrite of knowledge system"
```

---

## References

- `.ai/core/kup/README.md` — KUP system
- `.ai/core/registry/REGISTRY.md` — Knowledge registry
