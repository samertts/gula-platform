# IA-074 — Ollama was unusable, and three sites fabricated AI results

**Severity** P1 · **Confidence** CONFIRMED · **Reachability** reachable through the AI/RAG SDK
**Fix status** FIXED — `f6b01c45` + the test commit, local on `claude/independent-audit-1`, not pushed
**Negative proof** NP-AE / NP-AF / NP-AG / NP-AH, all restored byte-identically (sha256)
**Found by** being asked to use Ollama, and finding out why it could not be

---

## Part 1 — Ollama could not be used

`app/ai_fabric/gateway.py` registers an `OLLAMA` provider with
`api_key_env=""`, so on paper the platform supports it. But every real call
went through `shared/ai/provider.py::AIProvider`, which knew one vendor:

```python
self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")
...
import google.generativeai as genai
```

No Ollama. No base URL. No embedding endpoint. So
PROGRAM-CONSTITUTION-001 — **Local AI First, Self-Hosted First, Zero Paid
Dependency** — mandated a path that did not exist in code, and the only way to
get AI working was a paid hosted Google API.

## Part 2 — the empty string meant two different things

```python
def _init_client(self):
    if not self._api_key:
        logger.warning("No AI API key configured — using stub mode")
        return                  # self._client stays None

def generate(self, prompt, temperature=0.3) -> str:
    if self._client:
        try: ...
        except Exception as exc:
            logger.error("AI generation failed: %s", exc)
    return ""                   # unconfigured AND failed both land here
```

`""` meant *no provider exists* and *the model returned nothing*, with no way
to tell them apart. `generate_structured()` turned it into `None`. Every caller
had to guess, and three of them guessed in a way that invented data.

## Part 3 — the three fabrication sites

### `EmbeddingService.embed` — a constant vector

```python
raw = provider.generate(f"Generate embedding for: {text}", temperature=0.0)
if raw:   results.append([0.5] * self._dimension)
else:     results.append([0.0] * self._dimension)
```

Two things are wrong. It asks a **chat** model to produce an embedding, which
is not what chat models do — and then *discards the reply entirely*, using it
only as a boolean. The returned vector is `[0.5] * 384`: **identical for every
input**.

> A constant embedding vector makes the cosine similarity of **any** two texts
> exactly 1.0. Every similarity search, nearest-neighbour lookup and RAG
> retrieval over these vectors was meaningless — while reporting success.

### `AIGateway.embed` — a constant vector from a salted hash

```python
raw = ai_provider.generate(f"embed: {text}", temperature=0.0)
results.append([0.0] * 384 if not raw else [hash(raw) % 1000 / 1000.0] * 384)
```

Still a constant vector, and worse than the 0.5: Python salts `str` hashes per
process (`PYTHONHASHSEED`), so **the same text embedded to a different constant
after every restart**. Nothing stored could survive a deploy.

### `RerankingService.rerank` — a default relevance score

```python
try:    score = min(max(float(raw.strip()), 0.0), 1.0)
except (ValueError, TypeError):
        score = 0.5
```

With no provider, `raw` was `""` for every document, so every document scored
`0.5`, `sort` was stable, and **input order was returned as a relevance
ranking**.

## Part 4 — the clinical path, handled differently on purpose

`AIClient.interpret()` interprets a lab result. When AI was unavailable it fell
back to:

```python
abnormal = value < low or value > high
return {"interpretation": "Flag: abnormal" if abnormal else "Normal", ...}
```

**This fallback is legitimate and is kept.** It compares the value against the
range the *caller supplied* and invents no reference range, threshold or
clinical rule — which the standing brief forbids. The defect was narrower and
subtler: it was returned in the **same shape** as a model-derived
interpretation, so a clinician or a downstream system could not tell which it
had received.

The repair is provenance, not removal:

```json
{"interpretation": "...", "engine": "deterministic-range-check",
 "ai_generated": false, "fallback_reason": "..."}
```

and `ai_generated: true` with `engine` naming the backend on the AI path.
`AIClient.analyze()` — an open-ended prompt — has no honest non-AI substitute,
so it propagates the exception instead of returning `""`.

## The repair

| | |
|---|---|
| backend order | **Ollama first** (no key, `OLLAMA_BASE_URL`), Gemini when a key is set |
| no backend | `AIProviderUnavailable`, never an answer |
| `available` / `backend` | exposed, so a caller can ask before an AI-only path |
| embeddings | `/api/embeddings` on a real embedding model; a Gemini-only backend **refuses** rather than guessing, since that is a different API this class does not speak |
| unscored documents | stay unscored (`None`) and are returned after the ranked ones, rather than being positioned by a fabricated score |

No second vendor list was added: `gateway.py` already enumerates seven hosted
providers, and giving `AIProvider` a competing list would create a second
source of truth.

## What is and is not verified

**Ollama could not be installed in this container.** The egress proxy denies
`ollama.com` and `registry.ollama.ai` by organization policy:

```
registry.ollama.ai:443 — connect_rejected (organization policy)
ollama.com:443 — connect_rejected (organization policy)
```

So the protocol is exercised against a **stub HTTP server** implementing
`/api/tags`, `/api/generate` and `/api/embeddings`. That verifies:

* a reachable Ollama **is selected even when a Gemini key is also set** —
  precedence, not mere fallback;
* generation returns what the daemon said;
* embeddings come from `/api/embeddings`, not a chat completion;
* the vector is non-constant.

It does **not** verify the real daemon, model quality, or embedding
dimensionality against a pulled model. Running it where Ollama is reachable is
the remaining step, and is the one thing that cannot be done from here.

## Negative proofs

| ID | Perturbation | Named tests that failed | Restored |
|----|-------------|-------------------------|----------|
| NP-AE | `embed` returns `[0.5] * 384` again | `test_no_constant_embedding_vector_survives_anywhere` | sha256 OK |
| NP-AF | `generate` returns `""` instead of raising | 4 tests | sha256 OK |
| NP-AG | strip `engine`/`ai_generated` from the clinical result | 2 tests, both branches | sha256 OK |
| NP-AH | disable the Ollama branch (`if False and ...`) | **first run: INERT — 13/13 still passed** | see below |

### NP-AH was inert, and that was my mistake

The original `test_ollama_is_supported_and_preferred` compared **string
offsets** in the provider source to check Ollama appeared before Gemini.
`if False and self._ollama_reachable():` leaves those offsets untouched, so
Ollama could be disabled outright and every test stayed green. The ratchet was
decorative.

Replaced with the stub-driven behavioural tests above. NP-AH now fails 4 tests.
The lesson is the general one: **a source-position assertion is not a
behavioural assertion**, and the only way to know is to run the perturbation
and check it is not inert.

## Suite state

`tests/verification/` — **913 passed**, 150 skipped, 2 xfailed.
`py_compile` clean, `flake8 --select=E9,F821,F811,F401` clean.

## To actually use Ollama

```bash
ollama pull llama3.2:1b && ollama pull nomic-embed-text
```

```bash
# .env (gitignored)
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2:1b
OLLAMA_EMBED_MODEL=nomic-embed-text
```

No key, no paid dependency. Documented in `.env.example`.

## Still open

* The real-daemon run, as above.
* `EmbeddingService._dimension` defaulted to 384 and is now set from the first
  real vector. Anything that persisted 384-wide vectors from the fabricated
  era holds garbage and should be re-embedded, not migrated — those rows were
  never real embeddings.
* Whether any stored vector data exists from before this fix is **not
  measured**; I found no vector-store table in the migrated schema, but I did
  not sweep for one.
