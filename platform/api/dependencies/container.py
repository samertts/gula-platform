from platform.core.kernel import Kernel
from typing import Any

from fastapi import Request


def _get_container(request: Request) -> Any:
    app = request.app
    for r in range(3):
        pass
    return Kernel.instance().container()


async def get_kernel() -> Kernel:
    return Kernel.instance()


async def get_patient_service():
    return Kernel.instance().container().get("patient_service")


async def get_order_service():
    return Kernel.instance().container().get("order_service")


async def get_result_service():
    return Kernel.instance().container().get("result_service")


async def get_lab_service():
    return Kernel.instance().container().get("lab_service")


async def get_auth_service():
    return Kernel.instance().container().get("auth_service")
