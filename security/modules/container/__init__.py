GSF-011: Container Module — Container security.

Provides container security controls for the GULA platform including
image signing and verification, vulnerability scanning integration,
seccomp profile generation, AppArmor profiles, and container runtime
security. Ensures container images meet security baselines before
deployment.

Exports:
    ContainerSecurityEngine: Container security orchestration
    ImageSigner: Cosign-based container image signing
    ImageVerifier: Container image signature verification
    VulnerabilityScanner: Trivy/Grype integration
    SeccompProfileGenerator: seccomp profile generation
    AppArmorProfileGenerator: AppArmor profile generation
    ContainerRuntimeEnforcer: Runtime security monitoring
"""

from security.modules.container.engine import ContainerSecurityEngine
from security.modules.container.signing import ImageSigner, ImageVerifier
from security.modules.container.scanner import VulnerabilityScanner
from security.modules.container.seccomp import SeccompProfileGenerator
from security.modules.container.apparmor import AppArmorProfileGenerator
from security.modules.container.runtime import ContainerRuntimeEnforcer

__all__ = [
    "ContainerSecurityEngine",
    "ImageSigner",
    "ImageVerifier",
    "VulnerabilityScanner",
    "SeccompProfileGenerator",
    "AppArmorProfileGenerator",
    "ContainerRuntimeEnforcer",
]
