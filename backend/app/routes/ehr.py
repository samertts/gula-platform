
from fastapi import APIRouter

router=APIRouter()

@router.get("/ehr")

def ehr():

    return {

        "records":[

            {"type":"lab","test":"CBC","result":"normal"},

            {"type":"lab","test":"glucose","result":"105"}

        ]

    }

