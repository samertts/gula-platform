from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

logger = logging.getLogger("gula.ai_fabric.base")


@dataclass
class AIFabricEntity:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceRequest:
    prompt: str
    model: str = ""
    provider: str = ""
    temperature: float = 0.3
    max_tokens: int = 1024
    system_prompt: str = ""
    stream: bool = False
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class InferenceResponse:
    text: str
    model: str
    provider: str
    request_id: str
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    error: str = ""


class AIServiceProvider(Protocol):
    def chat(self, request: InferenceRequest) -> InferenceResponse: ...
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def is_available(self) -> bool: ...
