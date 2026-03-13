
from fastapi import APIRouter

router=APIRouter()

@router.get("/results")

def results():

    return [

        {"test":"CBC","value":"Normal"},
        {"test":"Glucose","value":"105"}

    ]

