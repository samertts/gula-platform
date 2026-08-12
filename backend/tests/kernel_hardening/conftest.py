from __future__ import annotations

import asyncio

import pytest

from app.kernel import Kernel, KernelConfig

pytestmark = [
    pytest.mark.kernel,
    pytest.mark.integration,
]


@pytest.fixture(autouse=True)
def reset_kernel():
    Kernel.reset_instance()
    yield
    Kernel.reset_instance()


@pytest.fixture()
def kernel() -> Kernel:
    config = KernelConfig(environment="test", debug=True)
    return Kernel(config=config)


@pytest.fixture()
def booted_kernel(kernel: Kernel) -> Kernel:
    asyncio.run(kernel.boot())
    return kernel


@pytest.fixture()
def running_kernel(booted_kernel: Kernel) -> Kernel:
    asyncio.run(booted_kernel.start())
    return booted_kernel
