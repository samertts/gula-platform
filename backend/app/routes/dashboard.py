
from fastapi import APIRouter

router=APIRouter()

@router.get("/dashboard")

def dashboard():

    return {

        "patients":1200,
        "samples":300,
        "tests":850,
        "critical":3

    }

