# GSF-005: Kubernetes Security Module

Implements Pod Security Standards (privileged/baseline/restricted), RBAC auditing, NetworkPolicy validation, and OPA constraint generation.

## Components

- `KubernetesSecurityManager` - Central security manager
  - Pod Security Standards enforcement
  - Pod security context validation
  - Network policy audit (default-deny verification)
  - RBAC audit (cluster roles, role bindings)
  - Service account security
  - Secret security
  - Admission controller validation
  - Resource quota validation (DoS prevention)
  - OPA/Gatekeeper constraint template generation
