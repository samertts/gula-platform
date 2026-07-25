from __future__ import annotations

from pydantic import BaseModel, Field


class ContainerSecurityProfile(BaseModel):
    privileged: bool = False
    capabilities: list[str] = Field(default_factory=lambda: ["NET_BIND_SERVICE", "CHOWN", "SETGID", "SETUID"])
    read_only_rootfs: bool = True
    run_as_non_root: bool = True
    seccomp_profile: str | None = "runtime/default"
    apparmor_profile: str | None = "runtime/default"
    allowed_hosts: list[str] = Field(default_factory=list)
    resource_limits: dict = Field(default_factory=lambda: {"cpu": "0.5", "memory": "512M", "pids": 100})


class ImageSecurityPolicy(BaseModel):
    allowed_registries: list[str] = Field(default_factory=lambda: ["docker.io", "ghcr.io", "gcr.io"])
    required_signatures: int = 1
    max_vulnerability_critical: int = 0
    max_vulnerability_high: int = 5
    require_sbom: bool = True
    freshness_max_days: int = 30


class DockerSecurityConfig(BaseModel):
    user_namespace: str = "host"
    cgroup_namespace: str = "private"
    pid_namespace: str = "private"
    ipc_namespace: str = "private"
    network_mode: str = "bridge"
    ulimits: dict = Field(default_factory=lambda: {"nofile": {"soft": 1024, "hard": 2048}, "nproc": {"soft": 100, "hard": 200}})
    security_opt_list: list[str] = Field(default_factory=lambda: ["no-new-privileges", "seccomp=unconfined"])
    no_new_privileges: bool = True
