"""Shared synthetic fixtures for Health Core development tests.

Every fixture here is in-memory and synthetic. No database session, no network,
no MPI client and no fixture may contain real patient data.
"""

from __future__ import annotations

import pytest
from app.health_core.identity.port import DEFAULT_SYNTHETIC_TENANT
from app.health_core.identity.synthetic import SyntheticPatientRegistry


@pytest.fixture
def synthetic_registry() -> SyntheticPatientRegistry:
    """A fresh, empty in-memory patient registry per test."""
    return SyntheticPatientRegistry()


@pytest.fixture
def synthetic_tenant() -> str:
    """The default synthetic tenant id."""
    return DEFAULT_SYNTHETIC_TENANT


@pytest.fixture
def synthetic_patient(synthetic_registry: SyntheticPatientRegistry, synthetic_tenant: str):
    """Register one synthetic patient and return its opaque reference."""
    return synthetic_registry.register_patient(tenant_id=synthetic_tenant, label="fixture-alpha")
