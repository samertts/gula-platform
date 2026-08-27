CONTRACTS_PACKAGE_VERSION = "1.0.0"
CONTRACTS_PACKAGE_DESCRIPTION = "Platform Contracts generation system — OpenAPI, AsyncAPI, JSON Schema, FHIR R4, GraphQL"

__all__ = [
    "CONTRACTS_PACKAGE_DESCRIPTION",
    "CONTRACTS_PACKAGE_VERSION",
    "EVENT_REGISTRY",
    "FHIR_PROFILES",
    "ContractGenerator",
    "CORE_CONTRACTS",
    "CONTRACTS_BY_DOMAIN",
    "ContractDefinition",
    "ContractEvidence",
    "ReadinessState",
    "get_contract",
    "require_transition",
    "ContractHealthReport",
    "EvidenceFinding",
    "evaluate_contract",
]

from .events import EVENT_REGISTRY
from .fhir import FHIR_PROFILES
from .generator import ContractGenerator
from .engineering_intelligence import ContractHealthReport, EvidenceFinding, evaluate_contract
from .clinical_core import (
    CORE_CONTRACTS,
    CONTRACTS_BY_DOMAIN,
    ContractDefinition,
    ContractEvidence,
    ReadinessState,
    get_contract,
    require_transition,
)
