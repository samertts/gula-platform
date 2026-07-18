import pytest
from platform.core.kernel import Kernel, KernelConfig


@pytest.fixture(scope="function")
def test_kernel():
    config = KernelConfig(
        name="test-kernel",
        version="1.0.0",
        environment="test",
    )
    kernel = Kernel(config)
    yield kernel
    kernel._running = False
    Kernel._instance = None


@pytest.fixture(scope="function")
def event_bus():
    from platform.core.event_bus import EventBus
    return EventBus()


@pytest.fixture(scope="function")
def command_bus():
    from platform.core.cqrs import CommandBus
    return CommandBus()


@pytest.fixture(scope="function")
def query_bus():
    from platform.core.cqrs import QueryBus
    return QueryBus()


@pytest.fixture(scope="function")
def workflow_engine():
    from platform.core.workflow import WorkflowEngine
    return WorkflowEngine()
