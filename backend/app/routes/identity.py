
from fastapi import APIRouter
import uuid

router=APIRouter()

@router.post("/identity/create")

def create_identity():

    return {

        "patient_uuid":str(uuid.uuid4())

    }

