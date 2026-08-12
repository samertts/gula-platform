# Container Security Report

## Dockerfile Analysis

### Backend Dockerfile (`backend/Dockerfile`)
| Check | Status | Notes |
|-------|--------|-------|
| Multi-stage build | ✅ | Reduces final image size |
| Non-root user | ✅ | Runs as `appuser` |
| No build tools in final | ✅ | Builder pattern |
| Healthcheck | ✅ | HTTP health check |
| Port exposure | ✅ | 10000 |
| ARG/ENV hygiene | ✅ | Environment-based config |
| **Missing:** | ❌ | No `SHELL` hardening (`SHELL ["/bin/bash", "-o", "pipefail", "-c"]`) |
| **Missing:** | ❌ | No `COPY --chown` for permissions |
| **Missing:** | ❌ | No `apt-get` clean-up combined with `rm -rf /var/lib/apt/lists/*` (already done) |

### Platform Dockerfile (`platform/Dockerfile`)
| Check | Status | Notes |
|-------|--------|-------|
| Non-root user | ❌ | Runs as root |
| Fix: | | Add `USER` directive |

### Services Dockerfiles
| Service | Non-root User | Missing |
|---------|---------------|---------|
| ai | ❌ | No USER directive |
| autonomous_manager | ❌ | No USER directive |
| device_bridge | ❌ | No USER directive |
| lab | ❌ | No USER directive |
| notification | ❌ | No USER directive |
| order | ❌ | No USER directive |
| patient | ❌ | No USER directive |
| result | ❌ | No USER directive |
| sample | ❌ | No USER directive |
| nhop-platform | ❌ | No USER directive |

### Frontend Dockerfiles (3rd party)
- `frontend-v2/node_modules/jsbarcode/Dockerfile` — runs as root

## Docker Compose Security

| Check | Status | Notes |
|-------|--------|-------|
| `no-new-privileges` | ✅ | Set on all services |
| Resource limits | ✅ | mem_limit, cpus configured |
| Internal network | ✅ | No external ports for most services |
| Healthchecks | ✅ | All services have healthchecks |
| Read-only root FS | ❌ | Not configured |
| AppArmor | ❌ | Not configured |
| Seccomp | ❌ | Not configured |
| Drop capabilities | ❌ | Not configured |

## Kubernetes Security

### Pod Security Standards (PSS)
| Workload | RunAsNonRoot | ReadOnlyRootFS | Seccomp | Capabilities |
|----------|-------------|----------------|---------|--------------|
| backend | ❌ | ❌ | ❌ | ❌ |
| frontend | ❌ | ❌ | ❌ | ❌ |
| gateway | ❌ | ❌ | ❌ | ❌ |
| microservices | ❌ | ❌ | ❌ | ❌ |
| postgres | ❌ | ❌ | ❌ | ❌ |
| rabbitmq | ❌ | ❌ | ❌ | ❌ |
| redis | ❌ | ❌ | ❌ | ❌ |

### Network Policies
| Check | Status |
|-------|--------|
| Network policies defined | ❌ |
| Default deny ingress | ❌ |
| Default deny egress | ❌ |
| mTLS enabled | ✅ (Linkerd installed but policies not enforced) |

## Issues Found

### CONT-01: All Containers Run as Root
**Severity:** Critical
**Impact:** Container breakout gives attacker root access to host
**Affected:** Multiple Dockerfiles and K8s deployments

### CONT-02: No Read-Only Root Filesystem
**Severity:** High
**Impact:** Writable filesystem increases attack surface for persistent compromise
**Affected:** All K8s deployments

### CONT-03: No Seccomp Profiles
**Severity:** High
**Impact:** No system call filtering, all syscalls allowed
**Affected:** All K8s deployments

### CONT-04: No Capability Dropping
**Severity:** High
**Impact:** Containers have unnecessary Linux capabilities
**Affected:** All K8s deployments

### CONT-05: Node Modules Dockerfile Uses Root
**Severity:** Medium
**Impact:** Unnecessary root access in build process
**Affected:** `frontend-v2/node_modules/jsbarcode/Dockerfile`

## Recommendations

1. Add security context to ALL K8s deployments
2. Add non-root user to ALL Dockerfiles
3. Configure seccomp profiles (RuntimeDefault)
4. Drop all capabilities except those required
5. Set readOnlyRootFilesystem: true
6. Add AppArmor profiles
7. Implement network policies (default deny)
8. Add PodDisruptionBudgets
9. Use distroless base images
10. Add container image scanning to CI/CD
