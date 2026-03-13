
from fastapi import APIRouter

router=APIRouter()

@router.get("/labs")

def labs():

    return [

        {"name":"CBC","status":"available"},
        {"name":"Glucose","status":"available"}

    ]

