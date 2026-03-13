
from fastapi import APIRouter
import uuid

router=APIRouter()

@router.post("/register")

def register():

    patient_uuid=str(uuid.uuid4())

    return {

        "patient_uuid":patient_uuid,

        "message":"account created"

    }

