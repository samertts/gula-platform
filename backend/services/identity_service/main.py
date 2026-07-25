from fastapi import FastAPI

app = FastAPI()

users = []


@app.post("/register")
def register(user: dict):

    users.append(user)

    return {"status": "registered"}


@app.post("/login")
def login(user: dict):

    for u in users:
        if u["username"] == user["username"]:
            return {"login": "ok"}

    return {"login": "failed"}
