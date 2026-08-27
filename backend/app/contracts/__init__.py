from .clinical_core import (
    CONTRACTS_BY_DOMAIN,
    CORE_CONTRACTS,
    ContractDefinition,
    ContractEvidence,
    ReadinessState,
    get_contract,
    require_transition,
)
from .engineering_intelligence import ContractHealthReport, EvidenceFinding, evaluate_contract
from .engineering_inventory import EngineeringInventoryReport, InventoryFinding, scan_repository
from .events import EVENT_REGISTRY
from .fhir import FHIR_PROFILES
from .generator import ContractGenerator

CONTRACTS_PACKAGE_DESCRIPTION = "Platform Contracts generation system — OpenAPI, AsyncAPI, JSON Schema, FHIR R4, GraphQL"

__all__ = [
    "CONTRACTS_BY_DOMAIN",
    "CONTRACTS_PACKAGE_DESCRIPTION",
    "CONTRACTS_PACKAGE_VERSION",
    "CORE_CONTRACTS",
    "EVENT_REGISTRY",
    "FHIR_PROFILES",
    "ContractDefinition",
    "ContractEvidence",
    "ContractGenerator",
    "ContractHealthReport",
    "EngineeringInventoryReport",
    "EvidenceFinding",
    "InventoryFinding",
    "ReadinessState",
    "evaluate_contract",
    "get_contract",
    "require_transition",
    "scan_repository",
]
