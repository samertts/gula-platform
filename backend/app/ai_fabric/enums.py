from __future__ import annotations

from app._compat import StrEnum


class AIProviderType(StrEnum):
    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    VLLM = "vllm"
    OPENROUTER = "openrouter"
    DEEPSEEK = "deepseek"
    HUGGINGFACE = "huggingface"


class AIModelCapability(StrEnum):
    CHAT = "chat"
    EMBEDDING = "embedding"
    RERANKING = "reranking"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"


class AgentStatus(StrEnum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    DEGRADED = "degraded"


class ModelLifecycle(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class ExecutionMode(StrEnum):
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    BATCH = "batch"
    STREAMING = "streaming"


class AIPermission(StrEnum):
    CLINICAL_READ = "clinical:read"
    CLINICAL_WRITE = "clinical:write"
    LAB_MANAGE = "lab:manage"
    PATIENT_VIEW = "patient:view"
    SYSTEM_ADMIN = "system:admin"
    AUDIT_VIEW = "audit:view"
    GOVERNANCE_MANAGE = "governance:manage"
