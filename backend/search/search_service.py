import redis
from fastapi import APIRouter

router = APIRouter()

r = redis.Redis(host="localhost",port=6379,decode_responses=True)

@router.get("/search")
def search(q:str):

    cached = r.get(q)

    if cached:
        return {"source":"cache","result":cached}

    # placeholder search logic
    result = f"search result for {q}"

    r.set(q,result)

    return {"source":"db","result":result}
