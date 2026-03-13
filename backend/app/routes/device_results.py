from fastapi import APIRouter
from ..gateways.lab_device_gateway import receive_device_result

router=APIRouter()

@router.post("/device/result")

def device_result(data:dict):

    return receive_device_result(
        data.get("sample"),
        data.get("test"),
        data.get("value")
    )
