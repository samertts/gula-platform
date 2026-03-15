from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():


return {"message": "Lab Platform Started"}


@app.get("/health")
def health():


return {"status": "ok"}
