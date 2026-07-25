GSF-020: Integrity Module — System integrity verification.

Provides system integrity controls for the GULA platform including
file integrity monitoring (FIM), configuration drift detection,
runtime integrity verification, kernel integrity monitoring, and
container image layer integrity. Ensures the platform has not been
tampered with at rest or during execution.

Exports:
    IntegrityEngine: System integrity orchestration
    FileIntegrityMonitor: File integrity monitoring (AIDE-like)
    ConfigDriftDetector: Configuration drift detection and alerting
    RuntimeVerifier: Runtime integrity verification (IMA)
    KernelMonitor: Kernel integrity and module monitoring
    LayerIntegrityVerifier: Container image layer integrity
"""

from security.modules.integrity.engine import IntegrityEngine
from security.modules.integrity.fim import FileIntegrityMonitor
from security.modules.integrity.config_drift import ConfigDriftDetector
from security.modules.integrity.runtime import RuntimeVerifier
from security.modules.integrity.kernel import KernelMonitor
from security.modules.integrity.layers import LayerIntegrityVerifier

__all__ = [
    "IntegrityEngine",
    "FileIntegrityMonitor",
    "ConfigDriftDetector",
    "RuntimeVerifier",
    "KernelMonitor",
    "LayerIntegrityVerifier",
]
