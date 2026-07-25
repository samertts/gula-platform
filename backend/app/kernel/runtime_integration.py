from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.kernel.runtime.lifecycle import LifecycleComponent

if TYPE_CHECKING:
    from app.kernel import Kernel

logger = logging.getLogger("gula.kernel.runtime_extensions")


def init_runtime_extensions(kernel: Kernel) -> None:
    logger.info("Initializing runtime extension modules")

    lifecycle = kernel.get_component("lifecycle_manager")

    _init_ai_runtime(kernel, lifecycle)
    _init_rules_runtime(kernel, lifecycle)
    _init_policy_runtime(kernel, lifecycle)
    _init_resource_manager(kernel, lifecycle)
    _init_runtime_governance(kernel, lifecycle)
    _init_runtime_security(kernel, lifecycle)
    _init_runtime_reliability(kernel, lifecycle)
    _init_runtime_observability(kernel, lifecycle)
    _init_runtime_performance(kernel, lifecycle)
    _init_runtime_digital_twin(kernel, lifecycle)
    _init_runtime_sdk(kernel, lifecycle)
    _init_runtime_validation(kernel, lifecycle)

    logger.info("Runtime extension modules initialized")


def register_runtime_routes(kernel: Kernel) -> None:
    logger.info("Registering runtime routes")
    from app.kernel.runtime_routes import router as runtime_router

    existing_routes = kernel.get_component("routes")
    if existing_routes is not None:
        existing_routes.include_router(runtime_router)
        logger.info("Runtime routes registered on existing router")
        return

    from fastapi import APIRouter

    router = APIRouter()
    router.include_router(runtime_router)
    kernel.register_component("runtime_router", router)
    logger.info("Runtime routes registered on standalone router")


def _init_ai_runtime(kernel: Kernel, lifecycle) -> None:
    from app.kernel.ai_runtime import AIRuntime

    ai = AIRuntime(kernel=kernel)
    ai.register_default_models()
    ai.load_model("gemini-pro")
    kernel.register_component("ai_runtime", ai)

    if lifecycle:
        comp = LifecycleComponent("ai_runtime")
        comp.on_start(lambda: ai.load_model("gemini-pro"))
        comp.on_stop(lambda: ai._loaded_models.clear())
        lifecycle.register(comp)
        logger.info("AI runtime initialized")


def _init_rules_runtime(kernel: Kernel, lifecycle) -> None:
    from app.kernel.rules_runtime import RulesRuntime

    rr = RulesRuntime(kernel=kernel)
    kernel.register_component("rules_runtime", rr)

    if lifecycle:
        comp = LifecycleComponent("rules_runtime")
        lifecycle.register(comp)
        logger.info("Rules runtime initialized")


def _init_policy_runtime(kernel: Kernel, lifecycle) -> None:
    from app.kernel.policy_runtime import PolicyRuntime

    pr = PolicyRuntime()
    kernel.register_component("policy_runtime", pr)

    if lifecycle:
        comp = LifecycleComponent("policy_runtime")
        lifecycle.register(comp)
        logger.info("Policy runtime initialized")


def _init_resource_manager(kernel: Kernel, lifecycle) -> None:
    from app.kernel.resource_manager import ResourceManager

    rm = ResourceManager()
    kernel.register_component("resource_manager", rm)

    if lifecycle:
        comp = LifecycleComponent("resource_manager")

        def _collect_metrics():
            rm.collect_metrics()

        comp.on_health(_collect_metrics)
        lifecycle.register(comp)
        logger.info("Resource manager initialized")


def _init_runtime_governance(kernel: Kernel, lifecycle) -> None:
    from app.kernel.runtime_governance import RuntimeGovernor

    governor = RuntimeGovernor()
    kernel.register_component("runtime_governor", governor)

    if lifecycle:
        comp = LifecycleComponent("runtime_governor")
        lifecycle.register(comp)
        logger.info("Runtime governor initialized")


def _init_runtime_security(kernel: Kernel, lifecycle) -> None:
    from app.kernel.runtime_security import (
        RuntimeAttestation,
        RuntimeSecureIsolation,
        SecretInjector,
    )

    isolation = RuntimeSecureIsolation()
    kernel.register_component("runtime_isolation", isolation)

    secrets = SecretInjector()
    kernel.register_component("secret_injector", secrets)

    attestation = RuntimeAttestation()
    kernel.register_component("runtime_attestation", attestation)

    if lifecycle:
        comp = LifecycleComponent("runtime_security")
        lifecycle.register(comp)
        logger.info("Runtime security initialized")


def _init_runtime_reliability(kernel: Kernel, lifecycle) -> None:
    from app.kernel.runtime_reliability import ReliabilityEngine

    re = ReliabilityEngine(kernel=kernel)
    kernel.register_component("reliability_engine", re)

    if lifecycle:
        comp = LifecycleComponent("reliability_engine")
        lifecycle.register(comp)
        logger.info("Reliability engine initialized")


def _init_runtime_observability(kernel: Kernel, lifecycle) -> None:
    from app.kernel.runtime_observability import RuntimeObserver

    observer = RuntimeObserver(kernel=kernel)
    kernel.register_component("runtime_observer", observer)

    if lifecycle:
        comp = LifecycleComponent("runtime_observer")

        def _register_topology():
            observer.topology.register_node(
                type(
                    "obj",
                    (object,),
                    {
                        "name": "gula-kernel",
                        "type": "service",
                        "version": kernel.config.version,
                        "to_dict": lambda self: {
                            "name": self.name,
                            "type": self.type,
                            "version": self.version,
                        },
                    },
                )(),
            )

        comp.on_start(_register_topology)
        lifecycle.register(comp)
        logger.info("Runtime observer initialized")


def _init_runtime_performance(kernel: Kernel, lifecycle) -> None:
    from app.kernel.runtime_performance import PerformanceOptimizer

    po = PerformanceOptimizer(kernel=kernel)
    kernel.register_component("performance_optimizer", po)

    if lifecycle:
        comp = LifecycleComponent("performance_optimizer")
        lifecycle.register(comp)
        logger.info("Performance optimizer initialized")


def _init_runtime_digital_twin(kernel: Kernel, lifecycle) -> None:
    from app.kernel.runtime_digital_twin import RuntimeDigitalTwin

    dt = RuntimeDigitalTwin(kernel=kernel)
    kernel.register_component("digital_twin", dt)

    if lifecycle:
        comp = LifecycleComponent("digital_twin")

        def _register_core():
            dt.register_entity(
                entity_id="kernel",
                entity_type="service",
                name=kernel.config.name,
                status="running",
                properties={
                    "version": kernel.config.version,
                    "environment": kernel.config.environment,
                },
                tags=["kernel", "core"],
            )

        comp.on_start(_register_core)
        lifecycle.register(comp)
        logger.info("Digital twin initialized")


def _init_runtime_sdk(kernel: Kernel, lifecycle) -> None:
    from app.kernel.runtime_sdk import RuntimeSDK

    sdk = RuntimeSDK(kernel=kernel)
    kernel.register_component("runtime_sdk", sdk)

    if lifecycle:
        comp = LifecycleComponent("runtime_sdk")
        lifecycle.register(comp)
        logger.info("Runtime SDK initialized")


def _init_runtime_validation(kernel: Kernel, lifecycle) -> None:
    from app.kernel.runtime_validation import RuntimeValidator

    validator = RuntimeValidator(kernel=kernel)
    kernel.register_component("runtime_validator", validator)

    if lifecycle:
        comp = LifecycleComponent("runtime_validator")
        lifecycle.register(comp)
        logger.info("Runtime validator initialized")
