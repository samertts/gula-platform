
from fastapi import APIRouter
from ai.ali_reza_engine import analyze

router=APIRouter()

@router.post("/api/medical/analyze")
def medical_analysis(data:dict):

    test=data.get("test")
    value=data.get("value")

    advice=analyze(test,value)

    return {
        "doctor":"Ali Reza",
        "analysis":advice
    }

