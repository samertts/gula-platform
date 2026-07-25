GSF-015: CI Module — CI/CD pipeline security.

Provides CI/CD pipeline security controls for the GULA platform including
pipeline integrity verification, SBOM generation (SPDX/CycloneDX),
SLSA compliance attestation, build environment hardening, and
dependency verification. Ensures the software supply chain for
GULA deployments meets security requirements.

Exports:
    CiSecurityEngine: CI/CD security orchestration
    PipelineIntegrityVerifier: CI pipeline integrity verification
    SbomGenerator: Software Bill of Materials generation
    SlsaAttestation: SLSA provenance and attestation
    BuildEnvironmentHardener: Build environment security hardening
    DependencyVerifier: Dependency chain verification
"""

from security.modules.ci.engine import CiSecurityEngine
from security.modules.ci.integrity import PipelineIntegrityVerifier
from security.modules.ci.sbom import SbomGenerator
from security.modules.ci.slsa import SlsaAttestation
from security.modules.ci.build_env import BuildEnvironmentHardener
from security.modules.ci.dependencies import DependencyVerifier

__all__ = [
    "CiSecurityEngine",
    "PipelineIntegrityVerifier",
    "SbomGenerator",
    "SlsaAttestation",
    "BuildEnvironmentHardener",
    "DependencyVerifier",
]
