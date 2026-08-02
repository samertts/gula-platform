# Government Portals — PROGRAM-05

Every authority is a registry object (`niam_gov_authorities`) — never hardcoded (Appendix-A).

| Authority | Type | Scope | Verification role |
|---|---|---|---|
| Ministry of Health | ministry | workforce, institutions, professional registry | employee import, institution verification |
| Ministry of Interior | ministry | national identity validation ONLY — never clinical data | identity review/approval/rejection |
| Governorate Health Directorate | directorate | facilities in governorate | facility verification |
| Professional Syndicate | syndicate | licensed professionals | license verify/update/suspend/restore |
| University | university | academic staff, students | academic verification |
| National Health Insurance | authority | insured citizens | insurance validation |
| Civil Registration | authority | national ID records | ID matching |
| Independent Authorities | authority | delegated scope | configurable |

## Scope isolation (Rule 6/7)

- Each authority sees only its own organizations, members, and verification queue.
- Ministry of Interior has identity-only scope; clinical records are never exposed to it.
- Approve / reject / suspend / restore decisions are audited per authority.
