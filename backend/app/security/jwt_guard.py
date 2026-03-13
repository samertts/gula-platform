
from fastapi import Request,HTTPException

def protect(request:Request):

    token=request.headers.get("Authorization")

    if not token:

        raise HTTPException(401,"Unauthorized")

    return True

