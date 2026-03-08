import os

import requests
from fastapi import FastAPI

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@app.get("/generate-api")
def generate_api(task: str):

    prompt = f"""
    Create FastAPI endpoint for:
    {task}
    """

    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={
            "model": "gpt-4.1-mini",
            "messages": [{"role": "user", "content": prompt}],
        },
    )

    return r.json()
