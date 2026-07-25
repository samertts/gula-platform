from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PodSecurityContext(BaseModel):
    run_as_user: int = 1000
    run_as_group: int = 1000
    fs_group: int = 1000
    se_linux_options: Optional[Dict[str, str]] = None
    supplemental_groups: List[int] = Field(default_factory=list)
    sysctls: List[Dict[str, str]] = Field(default_factory=list)


class PodSecurityPolicy(BaseModel):
    privileged: bool = False
    host_pid: bool = False
    host_ipc: bool = False
    host_network: bool = False
    allowed_capabilities: List[str] = Field(default_factory=lambda: ["NET_BIND_SERVICE", "CHOWN"])
    read_only_root: bool = True
    run_as_user_config: Dict[str, Any] = Field(
        default_factory=lambda: {"rule": "MustRunAsNonRoot", "ranges": [{"min": 1000, "max": 65535}]}
    )


class NetworkPolicySpec(BaseModel):
    pod_selector: Dict[str, str] = Field(default_factory=dict)
    ingress_rules: List[Dict[str, Any]] = Field(default_factory=list)
    egress_rules: List[Dict[str, Any]] = Field(default_factory=list)
    policy_types: List[str] = Field(default_factory=lambda: ["Ingress", "Egress"])


class K8sSecurityConfig(BaseModel):
    default_namespace_policies: str = "restricted"
    psp_enabled: bool = False
    network_policies_enabled: bool = True
    pod_security_standards: str = "restricted"
    opa_enabled: bool = False
    admission_controllers: List[str] = Field(
        default_factory=lambda: ["PodSecurity", "NodeRestriction", "AlwaysPullImages",
                                 "ServiceAccount", "NamespaceLifecycle", "ResourceQuota"]
    )
