"""
GULA Platform - AI Service
Executive Order 3: Local AI using Ollama only
Executive Order 4: No external AI providers
Executive Order 19: Multi-tier AI (Operational, Clinical, Population)
"""

import logging
import os
import time

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AI_PROVIDER   = os.getenv("AI_PROVIDER", "ollama")
AI_FALLBACK   = os.getenv("AI_FALLBACK", "false").lower() == "true"
OLLAMA_HOST   = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "llama3")

if AI_PROVIDER != "ollama":
    raise RuntimeError(
        f"Unsupported AI provider: {AI_PROVIDER}. "
        "Only 'ollama' is allowed (Executive Order 4)."
    )
if AI_FALLBACK:
    raise RuntimeError(
        "AI_FALLBACK must be false (Executive Order 4). "
        "External AI providers are disabled."
    )

app = FastAPI(
    title="GULA AI Service",
    description="Local AI using Ollama - No external providers",
    version="1.0.0",
)

_cors_origins = os.getenv("CORS_ORIGINS", "https://gula-platform.org,http://gula-platform.org").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Prometheus metrics
REQUEST_COUNT   = Counter("ai_requests_total", "Total AI requests", ["tier", "status"])
REQUEST_LATENCY = Histogram("ai_request_duration_seconds", "AI request duration", ["tier"])


class AIRequest(BaseModel):
    prompt: str
    tier: str = "operational"   # operational | clinical | population
    context: dict | None = None
    max_tokens: int | None = 1024


class AIResponse(BaseModel):
    result: str
    tier: str
    model: str
    provider: str = "ollama"
    latency_ms: float


def call_ollama(prompt: str, system_prompt: str | None = None, max_tokens: int = 1024) -> str:
    """Call local Ollama AI. No external providers allowed."""
    url = f"{OLLAMA_HOST}/api/generate"

    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.3,
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=90)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama service unavailable at {OLLAMA_HOST}. "
                   "Ensure Ollama is running and llama3 model is pulled."
        )
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AI TIER SYSTEM PROMPTS (Executive Order 19)
# =============================================================================

TIER_SYSTEM_PROMPTS = {
    "operational": """You are the Operational AI for GULA Medical Laboratory Platform.
Your role is to assist with day-to-day lab operations:
- Order management and prioritization
- Sample tracking and workflow optimization
- Quality control monitoring
- Device status and maintenance alerts
- Lab technician workflow assistance
Provide concise, actionable responses focused on operational efficiency.""",

    "clinical": """You are the Clinical AI for GULA Medical Laboratory Platform.
Your role is to support clinical decision-making:
- Interpret laboratory results within clinical context
- Flag abnormal values and critical results
- Suggest follow-up tests based on results
- Support diagnosis and treatment decisions
- Reference ranges and pathological significance
Always emphasize that AI analysis is advisory and requires physician validation.
IMPORTANT: Never replace clinical judgment. Always recommend physician review.""",

    "population": """You are the Population Health AI for GULA Medical Laboratory Platform.
Your role is to analyze population-level health data:
- Disease outbreak detection and tracking
- Epidemiological trend analysis
- Laboratory result pattern recognition across populations
- Public health risk assessment
- Geographic disease distribution analysis
- Preventive health recommendations
Focus on aggregate patterns while protecting individual patient privacy.""",
}


@app.get("/health")
def health():
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        ollama_ok = resp.status_code == 200
        models = [m["name"] for m in resp.json().get("models", [])] if ollama_ok else []
    except Exception:
        ollama_ok = False
        models = []

    return {
        "status": "healthy" if ollama_ok else "degraded",
        "provider": "ollama",
        "ollama_connected": ollama_ok,
        "available_models": models,
        "configured_model": OLLAMA_MODEL,
        "external_ai_disabled": True,
    }


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/analyze", response_model=AIResponse)
async def analyze(req: AIRequest):
    """Main AI analysis endpoint. Uses Ollama exclusively."""
    tier = req.tier
    if tier not in TIER_SYSTEM_PROMPTS:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}. Use: operational, clinical, population")

    system_prompt = TIER_SYSTEM_PROMPTS[tier]
    REQUEST_COUNT.labels(tier=tier, status="started").inc()

    start = time.time()
    try:
        with REQUEST_LATENCY.labels(tier=tier).time():
            result = call_ollama(req.prompt, system_prompt, req.max_tokens or 1024)
        latency_ms = (time.time() - start) * 1000
        REQUEST_COUNT.labels(tier=tier, status="success").inc()

        return AIResponse(
            result=result,
            tier=tier,
            model=OLLAMA_MODEL,
            provider="ollama",
            latency_ms=latency_ms,
        )
    except Exception:
        REQUEST_COUNT.labels(tier=tier, status="error").inc()
        raise


@app.post("/clinical/interpret")
async def clinical_interpret(req: AIRequest):
    """Clinical result interpretation (Clinical AI tier)."""
    req.tier = "clinical"
    return await analyze(req)


@app.post("/population/outbreak")
async def outbreak_detect(req: AIRequest):
    """Outbreak detection (Population AI tier)."""
    req.tier = "population"
    return await analyze(req)


@app.post("/operational/optimize")
async def operational_optimize(req: AIRequest):
    """Lab workflow optimization (Operational AI tier)."""
    req.tier = "operational"
    return await analyze(req)


@app.get("/models")
def list_models():
    """List available local models."""
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        resp.raise_for_status()
        return {"provider": "ollama", "models": resp.json().get("models", [])}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Cannot reach Ollama: {e}")
