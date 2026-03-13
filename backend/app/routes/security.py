
from fastapi import APIRouter

router=APIRouter()

@router.get("/security")

def security():

    return {"status":"secure"}

