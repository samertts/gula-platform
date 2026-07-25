from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from security.modules.kubernetes.models import (
    K8sSecurityConfig,
    NetworkPolicySpec,
    PodSecurityContext,
    PodSecurityPolicy,
)

logger = logging.getLogger(__name__)

POD_SECURITY_STANDARDS: Dict[str, Dict[str, Any]] = {
    "privileged": {
        "allowed_capabilities": ["ALL"],
        "allowed_host_paths": True,
        "allowed_volumes": ["*"],
        "run_as_user": {"rule": "RunAsAny"},
        "se_linux": {"rule": "RunAsAny"},
        "fs_group": {"rule": "RunAsAny"},
        "supplemental_groups": {"rule": "RunAsAny"},
    },
    "baseline": {
        "allowed_capabilities": ["CHOWN", "DAC_OVERRIDE", "FSETID", "FOWNER",
                                  "MKNOD", "NET_RAW", "SETGID", "SETUID",
                                  "SETFCAP", "SETPCAP", "NET_BIND_SERVICE", "SYS_CHROOT",
                                  "KILL", "AUDIT_WRITE"],
        "host_network": False,
        "host_pid": False,
        "host_ipc": False,
        "privileged_containers": False,
        "allowed_host_paths": False,
        "se_linux": {"rule": "RunAsAny"},
        "run_as_user": {"rule": "MustRunAsNonRoot"},
    },
    "restricted": {
        "allowed_capabilities": ["NET_BIND_SERVICE"],
        "host_network": False,
        "host_pid": False,
        "host_ipc": False,
        "privileged_containers": False,
        "allowed_host_paths": False,
        "se_linux": {"rule": "MustRunAs", "options": {"level": "s0:c123,c456"}},
        "run_as_user": {"rule": "MustRunAsNonRoot"},
        "fs_group": {"rule": "MustRunAs", "ranges": [{"min": 1, "max": 65535}]},
        "supplemental_groups": {"rule": "MustRunAs", "ranges": [{"min": 1, "max": 65535}]},
        "allow_privilege_escalation": False,
        "seccomp": {"type": "RuntimeDefault"},
    },
}

DANGEROUS_SYSCALLS: Set[str] = {
    "sys_admin", "sys_module", "sys_rawio", "sys_ptrace",
    "sys_boot", "sys_time", "sys_tty_config", "syslog",
    "sys_veto", "sys_pacct", "sys_setuid",
}

ESSENTIAL_CLUSTER_ROLES: Set[str] = {
    "cluster-admin", "admin", "edit", "view", "system:kube-scheduler",
    "system:kube-controller-manager", "system:node-proxier",
    "system:volume-scheduler", "system:node",
}


class RbacFinding(BaseModel):
    kind: str
    name: str
    namespace: str = ""
    subject_type: str = ""
    subject_name: str = ""
    issue: str
    severity: str


class PodFinding(BaseModel):
    resource_name: str
    namespace: str
    issues: List[str] = Field(default_factory=list)
    passed: bool = True


class NetworkPolicyFinding(BaseModel):
    namespace: str
    has_default_deny_ingress: bool = False
    has_default_deny_egress: bool = False
    policy_count: int = 0
    issues: List[str] = Field(default_factory=list)


class KubernetesSecurityReport(BaseModel):
    pod_findings: List[PodFinding] = Field(default_factory=list)
    rbac_findings: List[RbacFinding] = Field(default_factory=list)
    network_policy_findings: List[NetworkPolicyFinding] = Field(default_factory=list)
    overall_passed: bool = True


class KubernetesSecurityManager:
    def __init__(self, config: Optional[K8sSecurityConfig] = None):
        self.config = config or K8sSecurityConfig()

    def enforce_pod_security_standard(self, pod_spec: Dict[str, Any],
                                       standard: Optional[str] = None) -> Dict[str, Any]:
        std = standard or self.config.pod_security_standards
        rules = POD_SECURITY_STANDARDS.get(std)

        if not rules:
            return {"passed": False, "issues": [f"Unknown security standard: {std}"]}

        issues: List[str] = []
        passed = True

        containers = pod_spec.get("spec", {}).get("containers", []) + pod_spec.get("spec", {}).get("initContainers", [])
        for ctr in containers:
            sc = ctr.get("securityContext", {})
            if sc.get("privileged", False) and not rules.get("privileged_containers", True):
                issues.append(f"Container '{ctr.get('name', '')}' is privileged - not allowed in {std} profile")
                passed = False

            if sc.get("allowPrivilegeEscalation", True) and std == "restricted":
                issues.append(f"Container '{ctr.get('name', '')}' allows privilege escalation - must be false in restricted")
                passed = False

            caps = sc.get("capabilities", {}).get("add", [])
            allowed = set(rules.get("allowed_capabilities", []))
            for cap in caps:
                if cap.upper() not in {c.upper() for c in allowed}:
                    issues.append(f"Container '{ctr.get('name', '')}' has disallowed capability {cap} for {std}")
                    passed = False

            if std == "restricted" and "seccompProfile" not in sc:
                issues.append(f"Container '{ctr.get('name', '')}' missing seccompProfile in restricted")
                passed = False

        pod_sc = pod_spec.get("spec", {}).get("securityContext", {})
        if std == "restricted":
            if not pod_sc.get("runAsNonRoot", False):
                issues.append("Pod securityContext must set runAsNonRoot: true for restricted")
                passed = False

        if std == "baseline" or std == "restricted":
            if pod_spec.get("spec", {}).get("hostNetwork", False):
                issues.append(f"hostNetwork not allowed in {std} profile")
                passed = False
            if pod_spec.get("spec", {}).get("hostPID", False):
                issues.append(f"hostPID not allowed in {std} profile")
                passed = False
            if pod_spec.get("spec", {}).get("hostIPC", False):
                issues.append(f"hostIPC not allowed in {std} profile")
                passed = False

        return {"passed": passed, "issues": issues, "standard": std}

    def validate_pod_security_context(self, pod_spec: Dict[str, Any],
                                       context: Optional[PodSecurityContext] = None) -> Dict[str, Any]:
        ctx = context or PodSecurityContext()
        issues: List[str] = []
        passed = True

        spec = pod_spec.get("spec", {})
        sc = spec.get("securityContext", {})

        if sc.get("runAsUser", -1) <= 0:
            issues.append("runAsUser must be > 0 (non-root)")
            passed = False

        if sc.get("fsGroup", -1) <= 0:
            issues.append("fsGroup must be > 0")
            passed = False

        if not sc.get("seccompProfile", {}).get("type"):
            issues.append("seccompProfile not configured")
            passed = False

        if sc.get("seLinuxOptions"):
            pass
        elif not sc.get("seLinuxOptions") and sc.get("runAsNonRoot"):
            pass

        containers = spec.get("containers", [])
        for ctr in containers:
            ctr_sc = ctr.get("securityContext", {})
            if ctr_sc.get("runAsUser", -1) == 0:
                issues.append(f"Container '{ctr.get('name')}' runs as root (runAsUser: 0)")
                passed = False
            if not ctr_sc.get("readOnlyRootFilesystem", False):
                issues.append(f"Container '{ctr.get('name')}' does not have readOnlyRootFilesystem")
                passed = False
            if not ctr_sc.get("allowPrivilegeEscalation", True) is False:
                if sc.get("runAsNonRoot"):
                    pass
                else:
                    issues.append(f"Container '{ctr.get('name')}' should set allowPrivilegeEscalation: false")
                    passed = False

        return {"passed": passed, "issues": issues}

    def audit_network_policies(self, namespaces: Dict[str, List[NetworkPolicySpec]]) -> List[NetworkPolicyFinding]:
        findings: List[NetworkPolicyFinding] = []

        for ns, policies in namespaces.items():
            npf = NetworkPolicyFinding(namespace=ns, policy_count=len(policies))
            has_deny_all_ingress = False
            has_deny_all_egress = False

            for p in policies:
                if "Ingress" in p.policy_types:
                    if not p.ingress_rules:
                        has_deny_all_ingress = True
                if "Egress" in p.policy_types:
                    if not p.egress_rules:
                        has_deny_all_egress = True

            npf.has_default_deny_ingress = has_deny_all_ingress
            npf.has_default_deny_egress = has_deny_all_egress

            if not has_deny_all_ingress:
                npf.issues.append(f"Namespace '{ns}' missing default-deny ingress NetworkPolicy")
            if not has_deny_all_egress:
                npf.issues.append(f"Namespace '{ns}' missing default-deny egress NetworkPolicy")
            if policies:
                for p in policies:
                    for rule in p.ingress_rules:
                        for frm in rule.get("from", []):
                            if frm.get("ipBlock", {}).get("cidr") == "0.0.0.0/0":
                                npf.issues.append("NetworkPolicy allows traffic from 0.0.0.0/0")
            else:
                npf.issues.append(f"Namespace '{ns}' has no NetworkPolicies at all")

            findings.append(npf)

        return findings

    def audit_rbac(self, subjects: List[Dict[str, Any]], namespace: str = "") -> List[RbacFinding]:
        findings: List[RbacFinding] = []

        for subject in subjects:
            subject_kind = subject.get("kind", "User")
            subject_name = subject.get("name", "")
            role_ref = subject.get("roleRef", {}).get("name", "")
            role_kind = subject.get("roleRef", {}).get("kind", "Role")
            subject_ns = subject.get("namespace", namespace)

            if role_ref == "cluster-admin":
                findings.append(RbacFinding(
                    kind=role_kind,
                    name=role_ref,
                    namespace=subject_ns,
                    subject_type=subject_kind,
                    subject_name=subject_name,
                    issue=f"Subject '{subject_name}' has cluster-admin binding - excessive privilege",
                    severity="CRITICAL",
                ))

            if role_kind == "ClusterRole" and role_ref not in ESSENTIAL_CLUSTER_ROLES:
                pass

            if subject_kind == "ServiceAccount" and role_ref == "cluster-admin":
                findings.append(RbacFinding(
                    kind=role_kind,
                    name=role_ref,
                    namespace=subject_ns,
                    subject_type=subject_kind,
                    subject_name=subject_name,
                    issue="ServiceAccount should never be bound to cluster-admin",
                    severity="CRITICAL",
                ))

            if subject.get("namespace", "") == "kube-system" and role_ref not in ESSENTIAL_CLUSTER_ROLES:
                findings.append(RbacFinding(
                    kind=role_kind,
                    name=role_ref,
                    namespace=subject_ns,
                    subject_type=subject_kind,
                    subject_name=subject_name,
                    issue=f"Binding in kube-system namespace: {subject_name} -> {role_ref}",
                    severity="MEDIUM",
                ))

        wildcard_verbs = [s for s in subjects if s.get("rules", [{}])[0].get("verbs", []) == ["*"]]
        for s in wildcard_verbs:
            findings.append(RbacFinding(
                kind=s.get("roleRef", {}).get("kind", "Role"),
                name=s.get("roleRef", {}).get("name", ""),
                namespace=s.get("namespace", namespace),
                subject_type=s.get("kind", "User"),
                subject_name=s.get("name", ""),
                issue=f"Role '{s.get('roleRef', {}).get('name', '')}' uses wildcard verb '*'",
                severity="HIGH",
            ))

        return findings

    def validate_service_account(self, pod_spec: Dict[str, Any]) -> Dict[str, Any]:
        spec = pod_spec.get("spec", {})
        issues: List[str] = []
        passed = True

        if spec.get("automountServiceAccountToken", True):
            if "serviceAccountName" not in spec or not spec["serviceAccountName"]:
                issues.append("Default service account token automounted without explicit service account")
                passed = False

        sa_name = spec.get("serviceAccountName", "default")
        if sa_name == "default":
            issues.append("Using 'default' service account - create dedicated service accounts per pod")
            passed = False

        return {"passed": passed, "issues": issues}

    def validate_secret_security(self, secret_objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        issues: List[str] = []
        passed = True

        for secret in secret_objects:
            secret_type = secret.get("type", "Opaque")
            if secret_type == "kubernetes.io/dockerconfigjson":
                pass

            if not secret.get("metadata", {}).get("annotations", {}).get("kubernetes.io/description"):
                issues.append(f"Secret '{secret.get('metadata', {}).get('name', '')}' missing description annotation")

        return {"passed": passed, "issues": issues}

    def verify_admission_controllers(self) -> Dict[str, Any]:
        issues: List[str] = []
        passed = True
        required = ["PodSecurity", "NodeRestriction", "ServiceAccount", "NamespaceLifecycle"]
        recommended = ["MutatingAdmissionWebhook", "ValidatingAdmissionWebhook", "ResourceQuota",
                       "LimitRanger", "AlwaysPullImages"]

        configured = self.config.admission_controllers
        missing_required = [r for r in required if r not in configured]

        if missing_required:
            issues.append(f"Required admission controllers not enabled: {', '.join(missing_required)}")
            passed = False

        missing_recommended = [r for r in recommended if r not in configured]
        if missing_recommended:
            issues.append(f"Recommended admission controllers not enabled: {', '.join(missing_recommended)}")

        if "PodSecurityPolicy" in configured and self.config.pod_security_standards != "privileged":
            issues.append("PodSecurityPolicy admission controller is enabled but deprecated in K8s 1.25+")

        return {"passed": passed, "issues": issues, "configured": configured, "missing_required": missing_required}

    def validate_container_security_context(self, pod_spec: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []
        passed = True

        for container_type in ["containers", "initContainers"]:
            for ctr in pod_spec.get("spec", {}).get(container_type, []):
                sc = ctr.get("securityContext", {})
                ctr_name = ctr.get("name", "unknown")

                if sc.get("privileged", False):
                    issues.append(f"Container '{ctr_name}' is in privileged mode")
                    passed = False

                if sc.get("allowPrivilegeEscalation", True):
                    issues.append(f"Container '{ctr_name}' allows privilege escalation")
                    passed = False

                caps = sc.get("capabilities", {}).get("drop", [])
                caps_lower = [c.lower() for c in caps]
                if "all" not in caps_lower:
                    issues.append(f"Container '{ctr_name}' does not drop ALL capabilities")
                    passed = False

                if not sc.get("readOnlyRootFilesystem", False):
                    issues.append(f"Container '{ctr_name}' does not use readOnlyRootFilesystem")
                    passed = False

                if not sc.get("runAsNonRoot", False) and sc.get("runAsUser", 0) == 0:
                    issues.append(f"Container '{ctr_name}' runs as root")
                    passed = False

                seccomp = sc.get("seccompProfile", {})
                if seccomp.get("type", "") not in ("RuntimeDefault", "Localhost"):
                    issues.append(f"Container '{ctr_name}' missing seccomp profile")
                    passed = False

        return {"passed": passed, "issues": issues}

    def validate_resource_quotas(self, quota_spec: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []
        passed = True

        hard = quota_spec.get("spec", {}).get("hard", {})
        if "limits.cpu" not in hard:
            issues.append("ResourceQuota missing CPU limit")
            passed = False
        if "limits.memory" not in hard:
            issues.append("ResourceQuota missing memory limit")
            passed = False
        if "pods" not in hard:
            issues.append("ResourceQuota missing pod count limit")
            passed = False
        if "count/ingresses.extensions" not in hard and "count/ingress.networking.k8s.io" not in hard:
            pass

        if "requests.cpu" not in hard:
            issues.append("ResourceQuota missing CPU request")
        if "requests.memory" not in hard:
            issues.append("ResourceQuota missing memory request")

        return {"passed": passed, "issues": issues}

    def verify_namespace_isolation(self, namespace_config: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []
        passed = True

        labels = namespace_config.get("metadata", {}).get("labels", {})
        if "pod-security.kubernetes.io/enforce" not in labels:
            issues.append("Namespace missing pod-security.kubernetes.io/enforce label")
            passed = False

        enforce_level = labels.get("pod-security.kubernetes.io/enforce", "")
        if enforce_level not in ("restricted", "baseline", "privileged"):
            issues.append(f"Invalid pod security enforce level: '{enforce_level}'")
            passed = False
        elif enforce_level == "privileged" and self.config.pod_security_standards != "privileged":
            issues.append("Namespace allows privileged pods while cluster standard is restricted")
            passed = False

        return {"passed": passed, "issues": issues}

    def check_pod_priority_preemption(self, pod_spec: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []
        passed = True

        priority_class = pod_spec.get("spec", {}).get("priorityClassName", "")
        if priority_class in ("system-cluster-critical", "system-node-critical"):
            issues.append(f"Pod uses high priority class: '{priority_class}'")
            passed = False

        priority = pod_spec.get("spec", {}).get("priority", 0)
        if priority > 1000000:
            issues.append(f"Pod has very high priority value: {priority}")
            passed = False

        preemption = pod_spec.get("spec", {}).get("preemptionPolicy", "PreemptLowerPriority")
        if preemption == "PreemptLowerPriority" and priority > 0:
            issues.append(f"Pod has preemption policy '{preemption}' with priority > 0")

        return {"passed": passed, "issues": issues}

    def generate_opa_constraint_template(self, template_name: str, spec: Dict[str, Any]) -> str:
        template = {
            "apiVersion": "templates.gatekeeper.sh/v1beta1",
            "kind": "ConstraintTemplate",
            "metadata": {"name": template_name, "annotations": {"description": spec.get("description", "")}},
            "spec": {
                "crd": {"spec": {"names": {"kind": spec.get("kind", template_name)}}},
                "targets": [{
                    "target": "admission.k8s.gatekeeper.sh",
                    "rego": spec.get("rego", self._default_opa_rego(template_name, spec)),
                }],
            },
        }
        return json.dumps(template, indent=2)

    def _default_opa_rego(self, name: str, spec: Dict[str, Any]) -> str:
        return f"""
package {name}

violation[{{"msg": msg}}] {{
    input.review.object.kind == "Pod"
    not input.review.object.spec.securityContext.runAsNonRoot
    msg := "Containers must not run as root"
}}

violation[{{"msg": msg}}] {{
    input.review.object.kind == "Pod"
    container := input.review.object.spec.containers[_]
    container.securityContext.privileged
    msg := sprintf("Container %v is privileged", [container.name])
}}
""".strip()

    def full_security_audit(self, namespace_data: Dict[str, Dict[str, Any]]) -> KubernetesSecurityReport:
        pod_findings: List[PodFinding] = []
        rbac_findings: List[RbacFinding] = []
        overall_passed = True

        for ns, data in namespace_data.items():
            pods = data.get("pods", [])
            for pod in pods:
                name = pod.get("metadata", {}).get("name", "unknown")
                standard_check = self.enforce_pod_security_standard(pod)
                ctx_check = self.validate_pod_security_context(pod)
                sa_check = self.validate_service_account(pod)
                ctr_check = self.validate_container_security_context(pod)
                priority_check = self.check_pod_priority_preemption(pod)

                all_issues = standard_check["issues"] + ctx_check["issues"] + sa_check["issues"] + ctr_check["issues"] + priority_check["issues"]
                pod_passed = standard_check["passed"] and ctx_check["passed"] and sa_check["passed"] and ctr_check["passed"]

                if not pod_passed:
                    overall_passed = False

                pod_findings.append(PodFinding(
                    resource_name=name,
                    namespace=ns,
                    issues=all_issues,
                    passed=pod_passed,
                ))

            rbac_subjects = data.get("rbac_bindings", [])
            rbac_findings.extend(self.audit_rbac(rbac_subjects, ns))

        np_findings = self.audit_network_policies(
            {ns: data.get("network_policies", []) for ns, data in namespace_data.items()}
        )

        return KubernetesSecurityReport(
            pod_findings=pod_findings,
            rbac_findings=rbac_findings,
            network_policy_findings=np_findings,
            overall_passed=overall_passed,
        )
