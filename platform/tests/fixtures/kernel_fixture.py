import pytest
from platform.core.kernel import Kernel, KernelConfig


@pytest.fixture
def kernel():
    config = KernelConfig(
        name="test-kernel",
        version="1.0.0",
        environment="test",
    )
    instance = Kernel(config)
    yield instance
    instance._running = False
    Kernel._instance = None
