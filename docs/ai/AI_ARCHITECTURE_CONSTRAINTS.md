# AI Architecture Constraints

**Status:** Authoritative. Adopted 2026-05-11 production launch.
**Scope:** Every code path under `backend/app/ai/`, `backend/app/routes/ai*.py`,
`backend/app/gateways/google_ai.py`, `services/ai/`, `frontend-v2/src/components/GlobalAiAssistant.tsx`,
and any future AI-bearing route or service.

> These constraints are **non-negotiable**. Code that violates them must be
> rejected at review, regardless of feature urgency. See the corresponding
> security-invariant block in `CLAUDE.md`.

---

## 1. Approved AI architecture

GULA's AI subsystem is exactly the following composition, and nothing else:

```
┌──────────────────────────────────────────────────────────────────────┐
│  ┌────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────┐ │
│  │ Retrieval  │ → │  Medical     │ → │  Context     │ → │  LLM     │ │
│  │ (RAG)      │   │  Rules       │   │  Engine      │   │  (gate)  │ │
│  └────────────┘   └──────────────┘   └──────────────┘   └──────────┘ │
│        ↑                ↑                  ↑                 ↑       │
│        └────────────────┴──────────────────┴─────────────────┘       │
│                          Audit + Guardrails                          │
└──────────────────────────────────────────────────────────────────────┘
```

- **Retrieval (RAG)** — Look up curated clinical references, the lab's own
  policies, LOINC/SNOMED terminology, and the medical-terminology-normalized
  vocabulary. Embeddings live in a vector store (planned: Qdrant; until then,
  raw vectors are persisted as JSONB on `ai_retrieval_refs` so the audit
  trail is preserved).
- **Medical rules** — Deterministic rule pack (`backend/app/ai/guardrails.py`)
  that screens both inputs (block) and outputs (allow/escalate). Categorical
  rules ALWAYS win over LLM output.
- **Context engine** — Assembles tenant-scoped non-PII context (lab
  reference ranges, locale, language, recent biomarker patterns) for the
  prompt. Never includes raw identifiers.
- **LLM (gate)** — A third-party LLM (Gemini / Groq / Ollama, per
  `routes/ai.py` provider matrix) is called only for *interpretation and
  explanation*, never for action. The LLM is treated as untrusted: every
  response goes through guardrails before reaching the user.

## 2. AI role definition

AI is permitted to:
- **Interpret** an existing lab result in plain Arabic / English / Iraqi-Arabic
  ("هل القيمة طبيعية؟ ماذا تعني؟").
- **Educate** — Explain what a biomarker means in non-clinical language.
- **Navigate** — Help a user move through the platform ("how do I see my
  history?", "open the appointments view").
- **Augment decisions** — Summarise patterns and surface them to a clinician,
  who makes the final call.

AI is **forbidden** from:
- **Diagnosing autonomously.** No "you have X" output. Responses must phrase
  patterns as observations, never as diagnoses.
- **Prescribing or modifying treatment.** No medication suggestions, no dose
  changes, no test orders.
- **Writing to clinical state.** No row in `lab_results`, `lab_orders`,
  `patients`, or `samples` may be created or mutated by an AI code path. The
  AI Safety Layer (`routes/ai.py`) enforces this — see `AISandbox` whitelist.
- **Communicating with patients without a doctor in the loop** when the topic
  is treatment recommendation, prognosis, or differential diagnosis.

## 3. What we WILL NOT do

This list is exhaustive for the foreseeable horizon. Any change requires
formal re-approval at the architecture-board level:

1. **No full-model training.** We do not train foundation models.
2. **No custom LLM training.** We do not fine-tune base LLMs on patient data.
3. **No autonomous medical diagnosis.** Every clinically-impactful output is
   labelled as an *observation* and requires explicit doctor review when it
   exceeds the educational threshold.
4. **No AI-initiated patient communication.** Notifications and messages are
   always template-driven and human-gated.
5. **No silent retraining on production data.** The dataset captured per
   Phase 3 is **never** used to fine-tune an LLM without an explicit, dated
   approval entry in `docs/ai/TRAINING_APPROVALS.md` (the file must exist
   before any such approval is granted).

## 4. Data-protection contract (Phase 3 dataset)

The `ai_interactions` / `ai_feedback` / `ai_retrieval_refs` /
`ai_unresolved_questions` tables exist specifically to be safely sharable
within the GULA boundary for future RAG / retrieval-ranking / qualitative
analysis. To achieve that:

- **No PII columns.** The migration deliberately omits user_id, patient_id,
  national_id, phone, email, full_name, MRN, address. The schema **cannot**
  carry them.
- **Anonymous session ID is the only correlation key.** It is a hashed,
  rotating, per-tab identifier (see `frontend-v2/src/lib/telemetry.ts ::
  getAnonymousSessionId`). It is never derived from `user.id` or `patient.id`.
- **Tenant isolation on every row.** `lab_id` is stamped from the JWT at the
  backend boundary (`backend/app/routes/ai_telemetry.py`). Client-provided
  lab_id is ignored.
- **Prompts/responses may carry inline identifiers in free text.** The
  `prompt_redacted` flag exists for callers that have run a PII-redactor on
  the prompt before sending. A backend-side redaction pass is **planned**;
  until it ships, operators MUST:
  - Run the dataset in shadow mode (`ENABLE_AI_DATASET=false`) on prod, OR
  - Restrict the feature to pilot labs whose users have consented to research
    use of anonymised transcripts, OR
  - Pre-redact prompts on the client and set `prompt_redacted=true`.
  This is the **only acceptable launch posture** until the backend redactor
  exists.
- **Patient cards are never logged into interaction rows.** The
  `routes/patient_card.py` HMAC token system is excluded by name.
- **No raw embeddings in the dataset until Qdrant lands.** Vector data is
  currently stored as JSON only when it is needed for the audit trail (e.g.
  "we retrieved doc X with similarity 0.83"). Bulk embedding tables are not
  introduced in this phase.

## 5. Telemetry & feedback contract (Phase 2 + 4)

- PostHog: product analytics ONLY. We never send prompts/responses or
  retrieval refs to PostHog. Event props are limited to: language, intent,
  retrieval_count, latency_ms, signal (feedback). The `property_blacklist` in
  `telemetry.ts` is the last line of defence.
- Sentry: exception data ONLY. Breadcrumb URLs are stripped of query strings;
  the `beforeSend` hook drops `authorization` headers and `cookies`.
- Backend structured logs: include `request_id`, `user_id`, `lab_id`,
  `latency_ms`. They never carry prompts/responses unless DEBUG logging is
  explicitly enabled by an operator on the box.
- Feedback signals are constrained to a closed set: `helpful`,
  `not_helpful`, `unclear`, `need_doctor`, `incorrect_interpretation`. New
  signals require a product decision.

## 6. Flag-gating

| Flag                 | Default | Purpose                                                |
|----------------------|---------|--------------------------------------------------------|
| `ENABLE_AI_DATASET`  | `false` | Master switch for dataset writes/reads.                |
| `ENABLE_AI_FEEDBACK` | `false` | Sub-flag for the feedback endpoint specifically.       |

Routes return `503 AI_DATASET_DISABLED` / `AI_FEEDBACK_DISABLED` until on.

## 7. Review checklist for AI changes

Before merging any PR that touches an AI code path, the reviewer must
confirm, in writing, in the PR description:

- [ ] No new code path writes to `lab_results`, `lab_orders`, `patients`,
      or `samples` from an AI module.
- [ ] Every new prompt/response path goes through `ai/guardrails.py`.
- [ ] Any new column on the AI dataset tables does not store identifiers.
- [ ] If the PR collects new telemetry, the event name and props are listed
      in this document's § 5 above.
- [ ] If the PR introduces a new LLM provider, it is wired through
      `backend/app/gateways/`, not directly into routes.

Failure to confirm any of these means the PR cannot land.
