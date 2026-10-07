"""The AI provider can use Ollama, and never fabricates a vector or a score.

IA-074. ``shared/ai/provider.py`` was hardwired to one hosted vendor and
answered when it had no backend at all:

    self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")
    def _init_client(self):
        if not self._api_key:
            logger.warning("No AI API key configured — using stub mode")
            return
    def generate(self, prompt, temperature=0.3) -> str:
        if self._client: ...
        return ""        # unconfigured AND failed both land here

Two consequences, both measured.

**Ollama was unreachable in practice.** PROGRAM-CONSTITUTION-001 mandates Local
AI First / Self-Hosted First / Zero Paid Dependency, and
``app/ai_fabric/gateway.py`` registers an OLLAMA provider with
``api_key_env=""``. Every real call went through AIProvider, which knew only
Gemini. The constitutional first choice could not be used.

**Three downstream sites fabricated results from the empty string:**

* ``EmbeddingService.embed`` prompted a *chat* model with "Generate embedding
  for: {text}", discarded the reply and returned ``[0.5] * 384`` if anything
  came back, ``[0.0] * 384`` otherwise.
* ``AIGateway.embed`` returned ``[hash(raw) % 1000 / 1000.0] * 384``, or
  ``[0.0] * 384``. Python salts ``str`` hashes per process, so the same text
  embedded to a different constant after every restart.
* ``RerankingService.rerank`` scored every document ``0.5`` when parsing
  failed, so with no provider configured the "ranking" was input order.

A constant embedding vector makes the cosine similarity of ANY two texts 1.0.
Every similarity search, nearest-neighbour lookup and RAG retrieval over them
was meaningless while reporting success.

RATCHET. The regression here is not an exception returning -- it is someone
restoring a constant vector or a default score to make something "work". These
tests assert the raise, assert no constant-vector literal survives in the
sources, and assert the clinical interpretation says which engine produced it.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]
PROVIDER_FILE = REPO / "shared" / "ai" / "provider.py"
CLIENT_FILE = REPO / "shared" / "ai" / "client.py"
LOCAL_AI_FILE = REPO / "backend" / "app" / "ai_fabric" / "local_ai.py"
GATEWAY_FILE = REPO / "backend" / "app" / "ai_fabric" / "gateway.py"


def _unreachable_provider():
    """A provider with no backend: Ollama pointed at a dead port, no key."""
    from shared.ai.provider import AIProvider

    return AIProvider(api_key="", ollama_base_url="http://127.0.0.1:1")


# ── the provider itself ─────────────────────────────────────────────────────


def test_an_unconfigured_provider_reports_unavailable_rather_than_answering():
    from shared.ai.provider import AIProviderUnavailable

    provider = _unreachable_provider()
    assert provider.available is False
    assert provider.backend is None

    with pytest.raises(AIProviderUnavailable, match="no AI inference backend"):
        provider.generate("anything")


def test_generate_never_returns_the_empty_string_as_an_answer():
    """The specific defect: "" meant both "no provider" and "no reply"."""
    from shared.ai.provider import AIProviderUnavailable

    provider = _unreachable_provider()
    try:
        result = provider.generate("anything")
    except AIProviderUnavailable:
        return
    pytest.fail(f"generate() returned {result!r} with no backend configured")


def test_generate_structured_does_not_turn_an_outage_into_none():
    from shared.ai.provider import AIProviderUnavailable

    with pytest.raises(AIProviderUnavailable):
        _unreachable_provider().generate_structured("anything")


def test_embedding_raises_instead_of_inventing_a_vector():
    from shared.ai.provider import AIProviderUnavailable

    provider = _unreachable_provider()
    with pytest.raises(AIProviderUnavailable):
        provider.embed("some clinical text")
    with pytest.raises(AIProviderUnavailable):
        provider.embed_many(["a", "b"])


@pytest.fixture()
def ollama_stub():
    """A minimal HTTP server speaking Ollama's three endpoints.

    The real Ollama cannot be installed in this container -- the egress proxy
    denies ollama.com and registry.ollama.ai by organization policy -- so the
    protocol is exercised against a stub. This verifies that the provider
    SELECTS Ollama, calls the right paths and returns what the daemon says. It
    does NOT verify model quality or the real daemon's behaviour.
    """
    import json as _json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    calls: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # silence the default stderr spam
            pass

        def _send(self, payload: dict):
            body = _json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            calls.append(f"GET {self.path}")
            if self.path == "/api/tags":
                self._send({"models": [{"name": "llama3.2:1b"}]})
            else:
                self.send_error(404)

        def do_POST(self):
            calls.append(f"POST {self.path}")
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            if self.path == "/api/generate":
                self._send({"response": "stub-generated-text"})
            elif self.path == "/api/embeddings":
                # a non-constant vector, as a real model would give
                self._send({"embedding": [0.11, -0.42, 0.73, 0.05]})
            else:
                self.send_error(404)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", calls
    finally:
        server.shutdown()
        server.server_close()


def test_a_reachable_ollama_is_actually_selected(ollama_stub):
    """Behavioural, not positional.

    An earlier version of this test compared string offsets in the source to
    check Ollama came before Gemini. That ratchet was INERT: a negative proof
    that disabled the Ollama branch entirely (`if False and ...`) left all
    tests green, because the string positions were unchanged. This drives the
    selection instead.
    """
    from shared.ai.provider import AIProvider

    base_url, calls = ollama_stub
    # a Gemini key is ALSO set, so this proves precedence, not mere fallback
    provider = AIProvider(api_key="a-gemini-key-that-must-be-ignored", ollama_base_url=base_url)

    assert provider.available is True
    assert provider.backend == "ollama", (
        "Ollama was reachable and a Gemini key was present; Local AI First "
        "requires Ollama to win"
    )
    assert "GET /api/tags" in calls


def test_the_ollama_generation_path_returns_what_the_daemon_said(ollama_stub):
    from shared.ai.provider import AIProvider

    base_url, calls = ollama_stub
    provider = AIProvider(ollama_base_url=base_url)

    assert provider.generate("hello") == "stub-generated-text"
    assert "POST /api/generate" in calls


def test_the_ollama_embedding_path_uses_the_embedding_endpoint(ollama_stub):
    """And returns a real, non-constant vector."""
    from shared.ai.provider import AIProvider

    base_url, calls = ollama_stub
    vector = AIProvider(ollama_base_url=base_url).embed("clinical text")

    assert "POST /api/embeddings" in calls, "embeddings must not come from /api/generate"
    assert vector == [0.11, -0.42, 0.73, 0.05]
    # the defect's signature: every dimension identical
    assert len(set(vector)) > 1, "a constant vector is not an embedding"


def test_embed_many_returns_one_vector_per_text(ollama_stub):
    from shared.ai.provider import AIProvider

    base_url, _ = ollama_stub
    vectors = AIProvider(ollama_base_url=base_url).embed_many(["a", "b", "c"])
    assert len(vectors) == 3
    assert all(len(v) == 4 for v in vectors)


def test_ollama_uses_the_documented_endpoints_and_variable():
    source = PROVIDER_FILE.read_text()
    assert "OLLAMA_BASE_URL" in source
    assert "/api/embeddings" in source
    assert "/api/generate" in source


def test_a_gemini_backend_refuses_to_guess_an_embedding():
    """Gemini's embedding API is a different protocol this class does not speak.

    It must say so rather than fall back to the chat model and a constant.
    """
    source = PROVIDER_FILE.read_text()
    tree = ast.parse(source)
    embed = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "embed"
    )
    body = ast.get_source_segment(source, embed) or ""
    assert "embeddings require an embedding model" in body
    assert "raise" in body


# ── the clinical interpretation ─────────────────────────────────────────────


def test_the_clinical_interpretation_says_which_engine_produced_it():
    """The deterministic fallback is legitimate; being indistinguishable was not.

    It compares the value to the range the CALLER supplied and invents no
    reference range, threshold or clinical rule. The defect was that it was
    returned in the same shape as a model-derived interpretation, with nothing
    to tell them apart.
    """
    from shared.ai.client import AIClient

    client = AIClient(provider=_unreachable_provider())
    assert client.available is False

    result = client.interpret("Glucose", 9.9, (4.0, 6.0), "mmol/L")

    assert result["ai_generated"] is False
    assert result["engine"] == "deterministic-range-check"
    assert "fallback_reason" in result
    # and it still gives the honest clinical reading of the supplied range
    assert "abnormal" in result["interpretation"].lower()


def test_a_normal_value_is_also_labelled_as_non_ai():
    """The ratchet: the label must not appear only on the abnormal branch."""
    from shared.ai.client import AIClient

    result = AIClient(provider=_unreachable_provider()).interpret(
        "Glucose", 5.0, (4.0, 6.0), "mmol/L",
    )
    assert result["ai_generated"] is False
    assert result["interpretation"] == "Normal"


def test_open_ended_analysis_has_no_silent_substitute():
    """There is no honest non-AI answer to a free-text prompt, so it raises."""
    from shared.ai.client import AIClient
    from shared.ai.provider import AIProviderUnavailable

    with pytest.raises(AIProviderUnavailable):
        AIClient(provider=_unreachable_provider()).analyze("summarise this case")


# ── the ratchets over the sources ──────────────────────────────────────────


def test_no_constant_embedding_vector_survives_anywhere():
    """`[0.5] * 384`, `[0.0] * 384`, `[hash(...)] * 384` — all fabrications.

    A list-multiply of a single scalar into an embedding width is the shape of
    this defect, whatever the scalar is.
    """
    offenders = []
    for path in (LOCAL_AI_FILE, GATEWAY_FILE, PROVIDER_FILE):
        source = path.read_text()
        for node in ast.walk(ast.parse(source)):
            if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult)):
                continue
            left, right = node.left, node.right
            # a list of exactly one element, multiplied by something
            if isinstance(left, ast.List) and len(left.elts) == 1:
                segment = ast.get_source_segment(source, node) or ""
                offenders.append(f"{path.name}:{node.lineno}  {segment}")

    assert not offenders, (
        "a constant vector is being built; embeddings must come from an "
        "embedding model:\n" + "\n".join(offenders)
    )


def test_the_reranker_does_not_default_a_relevance_score():
    source = LOCAL_AI_FILE.read_text()
    tree = ast.parse(source)
    rerank = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "rerank"
    )
    body = ast.get_source_segment(source, rerank) or ""

    # strip comments, which quote the old `score = 0.5` on purpose
    code = "\n".join(
        line for line in body.splitlines() if not line.strip().startswith("#")
    )
    assert "score = 0.5" not in code, code
    assert "score = None" in code, "unscored documents must stay unscored"


def test_the_stub_mode_warning_is_gone_from_the_provider():
    """It announced a fallback that silently produced wrong answers.

    Checked against the string literals that are NOT docstrings. This module's
    docstring and the provider's own both quote the removed line on purpose, so
    a whole-file substring check passes on the quotation rather than the code --
    which is how this test failed on its first two runs.
    """
    source = PROVIDER_FILE.read_text()
    tree = ast.parse(source)

    # every node that can carry a docstring, and the literal that holds it
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            first = node.body[0] if node.body else None
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                docstrings.add(id(first.value))

    live_strings = [
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and id(n) not in docstrings
    ]

    offenders = [t for t in live_strings if "using stub mode" in t]
    assert not offenders, offenders
    # the ratchet: the file must still mention it somewhere, because the
    # docstring records what was removed and why
    assert "using stub mode" in source


def test_the_provider_exposes_availability_so_callers_can_ask():
    from shared.ai.client import AIClient
    from shared.ai.provider import AIProvider

    assert isinstance(AIProvider.available, property)
    assert isinstance(AIClient.available, property)
