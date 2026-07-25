from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

data = []


class Item(BaseModel):
    name: str
    value: str | None = None


@app.get("/")
def root():
    return {"service": "patient_service", "status": "running"}


@app.get("/list")
def list_items():
    return data


@app.post("/create")
def create_item(item: Item):
    data.append(item)
    return {"created": item}
