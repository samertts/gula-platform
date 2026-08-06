---
id: INCIDENT-000000
type: placeholder
title: "Incident Placeholder"
version: "1.0"
created: "2026-08-04"
status: active
confidence: 100%
tags: [incident, placeholder]
---

# Incident Records

This directory stores incident records. Each incident becomes a lesson,
and each lesson may become a skill.

## When an Incident Occurs

1. Create `INCIDENT-NNNNNN_<slug>.md` using incident template
2. Document symptoms, timeline, root cause, resolution
3. Create corresponding `LESSON-NNNNNN_<slug>.md`
4. Evaluate if a `SKILL-NNNNNN` should be created
5. Update `.ai/core/registry/REGISTRY.md`
6. Update `.ai/core/index/INDEX.md`

## Template

```yaml
---
id: INCIDENT-NNNNNN
type: incident
title: "Incident Title"
severity: [SEV1|SEV2|SEV3|SEV4]
created: "YYYY-MM-DD"
resolved: "YYYY-MM-DD"
status: [open|resolved|postmortem]
duration: "X hours Y minutes"
impact: [description of impact]
root_cause: [root cause]
resolution: [resolution]
lessons: [LESSON-NNNNNN]
skills: [SKILL-NNNNNN if created]
---
```

## Incident Severity Levels
- **SEV1**: Complete outage, data loss risk
- **SEV2**: Major degradation, partial outage
- **SEV3**: Minor degradation, workaround available
- **SEV4**: Cosmetic, no user impact
