# Capability contract

**PROGRAM-EXT-001, Phase 3.** Normative.

A capability is a reusable unit of behaviour the platform can enumerate, enable,
depend on and retire without reading its source. The contract is the metadata
that makes each of those four verbs possible.

## 1. Where it lives

`app/kernel/types.py::CapabilityDescriptor`, validated by
`app/kernel/extensibility.py::validate_descriptor`, registered in
`app/kernel/runtime/capability_registry.py::CapabilityRegistry`.

**No new registry was created.** GULA already loads 52 descriptors at boot. The
contract is a rule applied to the registry that exists, not a second store of
the same idea — that would be the precise mistake this programme exists to
prevent.

## 2. The required set

A capability registered after this contract MUST declare:

| Field | Why it cannot be derived from the code |
| --- | --- |
| `capability_id` | stable identity across renames; `name` is a label, this is the key |
| `name`, `version` | what to depend on, and which shape of it |
| `owner` | who answers a question about it at 02:00 |
| `description` | what it does, in one sentence, for someone who has not read it |
| `domain` | which boundary class it belongs to (see core-boundary.md) |
| `maturity` | how much evidence stands behind it — see module-lifecycle.md |
| `tenant_scope` | whose data it touches; the one property a signature never shows |
| `documentation` | where the prose is |
| `test_paths` | where the proof is |
| `module_path` | where the code is — without this the descriptor cannot be checked against reality at all |

And SHOULD declare, where they apply: `dependencies`, `required_permissions`,
`required_context`, `api_endpoints`, `events`, `data_contracts`, `audit`,
`feature_flag` + `flag_class`, `configuration`, `fhir_mappings`, `deprecation`.

## 3. The rules that are not just completeness

`validate_descriptor` enforces five properties beyond "the field is filled in".
Each exists because the absence of it has caused, or could cause, a real defect:

1. **A deprecating capability owes a destination.** `maturity` of `deprecated`
   or `retired` requires `deprecation.since_version`, `.removal_version` and
   `.replacement`. A capability that disappears without naming its successor
   breaks every consumer at once and tells none of them where to go.
2. **Sensitive data obliges an audit trail.** `audit.data_classification` in
   `{CLINICAL_SENSITIVE, PII, RESTRICTED}` requires `audit.writes_audit`. This
   is the one rule here that is a safety property rather than a documentation
   property, and it is the reason the audit fields exist at all.
3. **Tenancy and permissions must agree.** `tenant_scope = national_reference`
   means the data has no tenant; declaring tenant-evaluated permissions
   alongside it is ambiguous exactly where ambiguity is most expensive.
4. **A flag class must match maturity.** A `production` capability behind an
   `experimental` flag is either mislabelled or a rollout nobody finished.
5. **Types are types.** `maturity` and `tenant_scope` must be the enums, not
   strings that look like them.

## 4. The 52 that predate this

Every one of the 52 descriptors already in the registry fails the contract, and
all of them fail on the same four fields: `capability_id`, `documentation`,
`test_paths`, `module_path`.

That uniformity is the finding. The registry describes 52 capabilities and
points at no code, no tests and no documentation for any of them — so it is a
catalogue, not a contract, and nothing it says can currently be checked.

They are named in `extensibility.GRANDFATHERED` rather than exempted by a
wildcard. The guard asserts two things about that set: no capability outside it
may be registered incomplete, and the set itself may never gain a member.
Backfilling it is per-domain work with a per-domain owner, and it is not done
here.

## 5. Adding a capability

```python
from app.kernel.types import (
    CapabilityAudit, CapabilityDescriptor, CapabilityMaturity,
    FeatureFlagClass, TenantScope,
)

CapabilityDescriptor(
    capability_id="cap.referral_routing",
    name="referral_routing",
    version="1.0.0",
    owner="clinical-platform",
    description="Routes an outbound referral to an eligible receiving facility.",
    domain="clinical",
    maturity=CapabilityMaturity.EXPERIMENTAL,
    flag_class=FeatureFlagClass.EXPERIMENTAL,
    feature_flag="ENABLE_REFERRAL_ROUTING",
    tenant_scope=TenantScope.TENANT,
    required_permissions=["referrals.create"],
    required_context=["tenant_id", "facility_id", "actor_account_id"],
    audit=CapabilityAudit(
        writes_audit=True,
        audit_service="app.identity.services.canonical_audit.CanonicalAuditService",
        data_classification="CLINICAL_SENSITIVE",
        retention_days=3650,
    ),
    module_path="app/clinical/referral_routing",
    documentation=["docs/clinical/referral-routing.md"],
    test_paths=["backend/tests/test_referral_routing.py"],
)
```

Run `validate_descriptor` on it. An empty list is the contract met.

## 6. What this contract deliberately does not do

It does not load code, construct the capability, or check that `module_path`
exists on disk. Those are runtime concerns and adding them here would make a
metadata check depend on import success — which, given that nine of the ten
packages under `app/capabilities/` currently fail to import (NR-050), would make
the contract unusable on the day it shipped. The guard checks metadata; reachability is the
lifecycle's job.
