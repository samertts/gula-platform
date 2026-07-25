GSF-016: Supply Chain Module — Supply chain security.

Provides supply chain security controls for the GULA platform including
dependency verification, artifact attestation verification, provenance
tracking (SLSA), and Software Bill of Materials (SBOM) validation.
Ensures the integrity of third-party components used across the platform.

Note:
    This module lives in the "supply-chain" directory on the filesystem
    but is imported using the underscore alias:
        from security.modules.supply_chain import DependencyVerifier

Exports:
    SupplyChainSecurityEngine: Supply chain security orchestration
    DependencyVerifier: Dependency integrity verification
    AttestationVerifier: Artifact attestation verification (cosign, in-toto)
    ProvenanceTracker: SLSA provenance tracking
    SbomValidator: SBOM validation and policy enforcement
    ArtifactSigner: Artifact signing and verification
"""

from security.modules.supply_chain.engine import SupplyChainSecurityEngine
from security.modules.supply_chain.dependencies import DependencyVerifier
from security.modules.supply_chain.attestations import AttestationVerifier
from security.modules.supply_chain.provenance import ProvenanceTracker
from security.modules.supply_chain.sbom import SbomValidator
from security.modules.supply_chain.signing import ArtifactSigner

__all__ = [
    "SupplyChainSecurityEngine",
    "DependencyVerifier",
    "AttestationVerifier",
    "ProvenanceTracker",
    "SbomValidator",
    "ArtifactSigner",
]
