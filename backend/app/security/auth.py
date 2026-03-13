
from fastapi import HTTPException
from datetime import datetime,timedelta
import jwt

SECRET="GULA_SECRET"

def create_token(user):

    payload={
        "user":user,
        "exp":datetime.utcnow()+timedelta(hours=24)
    }

    return jwt.encode(payload,SECRET,algorithm="HS256")

def verify_token(token):

    try:

        return jwt.decode(token,SECRET,algorithms=["HS256"])

    except:

        raise HTTPException(401,"Invalid token")

