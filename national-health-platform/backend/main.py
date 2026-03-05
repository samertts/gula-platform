from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "National Health Lab Platform Running"}
