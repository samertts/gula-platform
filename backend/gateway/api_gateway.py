
from fastapi import FastAPI

app = FastAPI()

services = {
"patients":"http://localhost:8001",
"labs":"http://localhost:8002",
"orders":"http://localhost:8003",
"results":"http://localhost:8004",
"samples":"http://localhost:8005",
"notifications":"http://localhost:8006",
"identity":"http://localhost:8007"
}

@app.get("/")
def root():
    return {"gateway":"running"}

@app.get("/services")
def list_services():
    return services
