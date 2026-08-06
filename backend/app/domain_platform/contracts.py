"""PROGRAM-STABLE-004 — Cross-Domain Contracts (Phase 4).

Direct access between Domains is forbidden. The only legal communication
channels are versioned contracts: public REST APIs, FHIR APIs, HL7, and
events. Every contract MUST be versioned, documented, and tested before it
can be published. The CrossDomainGateway is the single enforcement point.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain_platform.core import (
    ALLOWED_CROSS_DOMAIN_CHANNELS,
    ContractKind,
    DomainContract,
)
from app.domain_platform.versioning import InvalidVersionError, parse_version


@dataclass
class ContractEnforcementReport:
    """Result of enforcing the cross-domain contract rules."""

    contracts: list[DomainContract] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)

    @property
    def passes(self) -> bool:
        return not self.violations

    def to_dict(self) -> dict[str, Any]:
        return {
            "contracts": [c.to_dict() for c in self.contracts],
            "violations": self.violations,
            "passes": self.passes,
        }


class ContractRegistry:
    """Registry of versioned cross-domain contracts.

    Rules enforced on registration:

      * contract_id is unique.
      * every contract declares kind in {rest, fhir, hl7, event}.
      * every contract has a SemVer version.
      * every contract has documentation (documentation_url non-empty).
      * every contract has a test reference (endpoint points to a tested
        surface; test presence is asserted by the certification engine).
      * provider and consumer are distinct Domains.
    """

    def __init__(self) -> None:
        self._contracts: dict[str, DomainContract] = {}
        self.violations: list[str] = []

    def register(self, contract: DomainContract) -> DomainContract:
        if contract.contract_id in self._contracts:
            self.violations.append(f"duplicate contract_id '{contract.contract_id}'")
            raise ValueError(f"contract '{contract.contract_id}' already registered")
        if contract.kind not in ContractKind:
            self.violations.append(
                f"contract '{contract.contract_id}' has unsupported kind '{contract.kind}'"
            )
            raise ValueError(f"unsupported contract kind '{contract.kind}'")
        try:
            parse_version(contract.version)
        except InvalidVersionError as exc:
            self.violations.append(f"contract '{contract.contract_id}': {exc}")
            raise
        if contract.provider_domain == contract.consumer_domain:
            self.violations.append(
                f"contract '{contract.contract_id}' must span two distinct Domains"
            )
            raise ValueError("provider and consumer must be distinct Domains")
        if not contract.documentation_url:
            self.violations.append(
                f"contract '{contract.contract_id}' is not documented"
            )
            raise ValueError("every contract must be documented")
        if not contract.endpoint:
            self.violations.append(
                f"contract '{contract.contract_id}' is not wired to a tested endpoint"
            )
            raise ValueError("every contract must declare a tested endpoint")
        self._contracts[contract.contract_id] = contract
        return contract

    def get(self, contract_id: str) -> DomainContract | None:
        return self._contracts.get(contract_id)

    def list(self, domain_code: str | None = None) -> list[DomainContract]:
        contracts = list(self._contracts.values())
        if domain_code:
            contracts = [
                c
                for c in contracts
                if c.provider_domain == domain_code or c.consumer_domain == domain_code
            ]
        return contracts

    def enforce(self) -> ContractEnforcementReport:
        return ContractEnforcementReport(
            contracts=list(self._contracts.values()),
            violations=list(self.violations),
        )


class CrossDomainGateway:
    """The ONLY legal path for one Domain to reach another.

    A Domain never imports another Domain's modules. Instead it uses the
    gateway to communicate through the declared channel (public API, FHIR,
    HL7, or event). This preserves Domain Sovereignty at runtime.
    """

    def __init__(self, registry: ContractRegistry | None = None) -> None:
        self.registry = registry or ContractRegistry()

    def channel_for(self, kind: ContractKind) -> str:
        mapping: dict[ContractKind, str] = {
            ContractKind.rest: "public_api",
            ContractKind.fhir: "fhir_api",
            ContractKind.hl7: "hl7",
            ContractKind.event: "event_bus",
        }
        channel = mapping.get(kind)
        if channel not in ALLOWED_CROSS_DOMAIN_CHANNELS:
            raise ValueError(f"cross-domain channel '{channel}' is forbidden")
        return channel

    def resolve(
        self, provider_domain: str, consumer_domain: str, kind: ContractKind
    ) -> DomainContract | None:
        """Resolve the published contract a consumer may legally use."""
        for contract in self.registry.list(consumer_domain):
            if (
                contract.provider_domain == provider_domain
                and contract.kind == kind
                and contract.status == "published"
            ):
                return contract
        return None

    def assert_allowed(self, provider_domain: str, consumer_domain: str, kind: ContractKind) -> str:
        """Raise when the consumer has no published contract for the channel."""
        self.channel_for(kind)
        contract = self.resolve(provider_domain, consumer_domain, kind)
        if contract is None:
            raise PermissionError(
                f"domain '{consumer_domain}' has no published contract to "
                f"'{provider_domain}' over channel '{self.channel_for(kind)}'"
            )
        return f"{contract.contract_id}@{contract.version}"
