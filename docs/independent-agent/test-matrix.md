# Test matrix — what this pass verified, and how

"Proof" is reserved for a claim measured against a real artifact. Everything else
is named for what it is.

| Area | Probe | Strength | Result |
|---|---|---|---|
| SQL injection | grep for f-string / `%` interpolation inside `text()` / `execute()` over `app/` | candidate sweep; absence of a pattern, not proof of parameterisation everywhere | 0 sites |
| Unsafe deserialization | grep for `pickle.loads`, `eval(`, `exec(`, unsafe `yaml.load` | candidate sweep | 0 uses |
| Clinical integrity — Invariant #6 | read every `LabResult` write path; check the compare-and-swap | read, not executed | CAS present; no bypassing update path |
| Tenant isolation — `app/reference` | AST over route signatures + grep for the principal + served-path check | measured: AST + assembled app | 4 handlers client-scoped; package unserved |
| Tenant isolation — served surface | tenant parameters over 1794 served operations via OpenAPI | measured inventory | 70 operations; 2 verified correct, 68 unverified |
| Citizen PHI authorization | read `require_citizen_relationship` and its binding | read the effective dependency | correct |
| Environment integrity | same suite run with the database up and killed | executed, both states | 13/457/0 up; 17/370/83 killed |
| Test tripwires added | `tests/independent/test_reference_package_tenant_scope.py` | 3 tests, pass; ruff clean | IA-001 tripwired |

## Not attempted, and why

* **Distributed / offline synchronization, CRDT, Merkle, vector clocks** — the
  brief asks for conflict scenarios across two facilities. Not attempted: the
  tables those paths write are inside RB-2/RB-3, so a scenario would fail on a
  missing table and prove nothing about conflict resolution. Sequence this after
  the schema is buildable.
* **`EXPLAIN ANALYZE` performance work** — requires a populated database at
  realistic scale; the available databases are structural fixtures with ~0 rows,
  so any plan would be a seq-scan on an empty table and would mislead.
* **Chaos (Redis / RabbitMQ down)** — neither is running in this container, so
  "fails safely" could not be distinguished from "was never reached".
