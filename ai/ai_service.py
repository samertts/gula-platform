import os

import requests
from fastapi import FastAPI

app = FastAPI(title="Lab Platform AI Gateway")

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
HF_KEY = os.getenv("HUGGINGFACE_API_KEY")


@app.get("/")
def home():
    return {"service": "AI Gateway", "status": "running"}


# -----------------------------
# DeepSeek
# -----------------------------


def ask_deepseek(text):

    url = "https://api.deepseek.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a medical laboratory AI assistant."},
            {"role": "user", "content": text},
        ],
    }

    r = requests.post(url, headers=headers, json=data)

    return r.json()


# -----------------------------
# Gemini
# -----------------------------


def ask_gemini(text):

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"

    data = {"contents": [{"parts": [{"text": text}]}]}

    r = requests.post(url, json=data)

    return r.json()


# -----------------------------
# HuggingFace
# -----------------------------


def ask_huggingface(text):

    url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct"

    headers = {"Authorization": f"Bearer {HF_KEY}"}

    r = requests.post(url, headers=headers, json={"inputs": text})

    return r.json()


# -----------------------------
# AI Router
# -----------------------------


@app.post("/ai")
def ai_router(text: str, task: str = "general"):

    if task == "code":
        return ask_deepseek(text)

    if task == "research":
        return ask_gemini(text)

    if task == "model":
        return ask_huggingface(text)

    return ask_deepseek(text)


# -----------------------------
# Medical Analyzer
# -----------------------------


@app.post("/analyze-lab")
def analyze_lab(text: str):

    prompt = f"""
You are a medical laboratory AI.

Analyze the following lab results and give interpretation:

{text}
"""

    return ask_deepseek(prompt)


# -----------------------------
# AI Builder
# -----------------------------


@app.post("/build")
def build_system(task: str):

    prompt = f"""
You are a senior software architect.

Generate backend code and database structure for:

{task}

Stack:
FastAPI
PostgreSQL
Docker
"""

    try:
        return ask_deepseek(prompt)
    except Exception:
        return {"error": "AI service unavailable"}


# -----------------------------
# CBC Analyzer
# -----------------------------


@app.post("/analyze-cbc")
def analyze_cbc(hb: float, wbc: float, platelets: float):

    prompt = f"""
You are a medical laboratory specialist.

Interpret the following CBC values:

Hemoglobin: {hb}
WBC: {wbc}
Platelets: {platelets}

Explain if values are normal or abnormal and possible causes.
"""

    return ask_deepseek(prompt)


# -----------------------------
# AI Agent
# -----------------------------


@app.post("/agent")
def agent(task: str):

    prompt = f"""
You are a senior AI engineer working on a National Medical Laboratory Platform.

Tech stack:
FastAPI
PostgreSQL
Docker
Redis
Nginx

Task:
{task}

Respond with structured steps and code when needed.
"""

    try:
        return ask_deepseek(prompt)
    except Exception:
        return {"error": "AI service unavailable"}
