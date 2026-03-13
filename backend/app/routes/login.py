
from fastapi import APIRouter
from pydantic import BaseModel
from ..security.auth import create_token

router=APIRouter()

class Login(BaseModel):

    username:str
    password:str

@router.post("/login")

def login(data:Login):

    token=create_token(data.username)

    return {"token":token}

