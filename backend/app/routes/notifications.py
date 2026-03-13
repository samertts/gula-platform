
from fastapi import APIRouter

router=APIRouter()

@router.post("/notify")

def notify():

    return {"status":"sent"}

