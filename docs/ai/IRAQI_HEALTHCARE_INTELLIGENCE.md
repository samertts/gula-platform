# Iraqi Healthcare Intelligence Collection (Phase 6)

**Status:** Initial scope adopted 2026-05-11 production launch.
**Goal:** Build, over time, a sovereign, anonymised, sharable-within-GULA
dataset of how Iraqi clinicians and citizens *actually* use a medical
laboratory platform — what they ask, what they misunderstand, where the
system fails them, and how language varies across regions.

This is **not** a research dataset. It is an *operational* dataset whose
primary use is improving GULA's RAG retrieval, navigation flows, and
educational copy. Secondary research use requires a separate consent and
governance regime (see `docs/sndhs/` and § 5 below).

---

## 1. Why we collect this

Iraq does not have a published, open, Arabic-first dataset of lab-platform
interaction patterns. Every product decision today either imports an
English-centric assumption or relies on individual practitioner intuition.

Concretely, the questions we cannot answer today and that the dataset is
designed to answer:

1. **Which biomarkers do citizens ask about most**, regardless of clinical
   significance? (Drives educational content priority.)
2. **What words do Iraqi Arabic speakers use** for "creatinine", "fasting
   glucose", "WBC differential"? (Drives the normalised-terminology table.)
3. **Which AI explanations get marked `unclear` or `need_doctor`?** (Drives
   prompt-engineering iterations and identifies escalation cliffs.)
4. **Which navigation flows get abandoned before completion?** (PostHog
   funnel data, not in the AI dataset itself.)
5. **Which regions exhibit which usage patterns?** (Regional `region` column
   on `ai_interactions` — Baghdad vs Basra vs Erbil — without ever storing
   user identity.)
6. **Which questions go unresolved?** (`ai_unresolved_questions` is the
   explicit "I asked, AI couldn't answer" log.)

## 2. The dataset surface (recap from migration `20260511_0001`)

| Table                            | Purpose                                                  | PII? |
|----------------------------------|----------------------------------------------------------|------|
| `ai_interactions`                | Every user↔AI exchange, language, intent, prompt, response, latency | No — see § 4 of `AI_ARCHITECTURE_CONSTRAINTS.md` |
| `ai_retrieval_refs`              | RAG audit trail (which doc/chunk supported a response)  | No |
| `ai_feedback`                    | Explicit user signal: helpful / not_helpful / unclear / need_doctor / incorrect_interpretation | No |
| `ai_unresolved_questions`        | Explicit "this didn't get answered" log                  | No |
| `medical_terminology_normalized` | Curated AR / AR-IQ / EN vocabulary with LOINC/SNOMED codes | No (reference data) |

Tenant isolation by `lab_id` is enforced on all writes; the terminology
table is global.

## 3. What "Iraqi Arabic" means here

The `language` column carries an IETF tag — typically `ar`, `ar-IQ`,
`ar-EG`, `en`, `ku-IQ` (Kurdish — Iraq). The frontend's
`LanguageContext` is the source of truth for this value.

The `region` column is a free-form lowercase string drawn from the lab's
governorate / city assignment, never from the user's input or geolocation.

For terminology, the `medical_terminology_normalized` table carries three
parallel columns:

- `term_en`    — canonical English (e.g. "Fasting Plasma Glucose")
- `term_ar`    — Modern Standard Arabic ("الجلوكوز في الدم صائم")
- `term_ar_iq` — Iraqi-Arabic-dialect variant if it materially differs

Synonyms (regional, colloquial, abbreviation, vendor-instrument variants)
go in the `synonyms` JSON array. Operational rule: if the same biomarker
shows up under three different spellings across three labs in a month, all
three go in `synonyms` for that row.

## 4. Operational collection workflow

### 4.1 Shadow mode (default at launch)

```
ENABLE_AI_DATASET=false
ENABLE_AI_FEEDBACK=false
```

Routes return 503 with `AI_DATASET_DISABLED`. Tables exist (migration ran)
but no rows are written. **This is the production-launch posture for
2026-05-11.**

### 4.2 Pilot mode (week 1 post-launch — by approval)

Enable on one pilot lab only:

```
ENABLE_AI_DATASET=true
ENABLE_AI_FEEDBACK=true
```

Communicate to pilot-lab users via the standard notification surface that
anonymised interaction transcripts will be retained for product improvement.
Until the backend-side prompt redactor exists, this is conditional on
client-side `prompt_redacted=true` for any prompt that may carry free-text
identifiers.

### 4.3 Steady-state (post-redactor)

Once the backend redactor ships, enable platform-wide. The redactor must:

- Run **before** the prompt is persisted to `ai_interactions`.
- Strip free-text mentions of: national ID patterns (`\d{12}`), phone
  numbers, full names matching the `patients` table for the calling lab,
  email-like strings.
- Set `prompt_redacted=true` after success.
- Fail closed: on redactor error, the interaction row is written with
  `status='guardrail_blocked'` and `prompt` NULL.

## 5. Secondary-use governance

Any use of this dataset beyond GULA's own retrieval / ranking / copy
improvements requires:

1. A signed entry in `docs/ai/TRAINING_APPROVALS.md` (file does not yet
   exist — must be created and signed before the first such approval).
2. Cross-check with `docs/sndhs/` governance.
3. Lab-side consent confirmation: have the pilot labs opted-in to research
   secondary use? (Stored on `lab_subscriptions.research_consent` — to be
   added in a future migration if/when needed.)

In particular: **no LLM fine-tuning** on this dataset is approved by
default. See § 3.1 of `AI_ARCHITECTURE_CONSTRAINTS.md`.

## 6. KPI surfacing

For operators, the `GET /api/ai/dataset/summary` endpoint exposes
per-lab aggregates:

```json
{
  "lab_id": 7,
  "interactions_total": 1842,
  "feedback_total": 311,
  "unresolved_open": 22,
  "feedback_breakdown": {
    "helpful":      214,
    "not_helpful":   42,
    "unclear":       38,
    "need_doctor":   12,
    "incorrect_interpretation": 5
  }
}
```

These are intentionally narrow; a richer analytics surface lives in
PostHog. Operator dashboards should pull both.

## 7. Out of scope for this phase

- **Embedding store / Qdrant.** Vectors will be stored once Qdrant is
  provisioned. Until then, `ai_retrieval_refs` holds only doc/chunk
  references, not the embeddings themselves.
- **A separate consent record per interaction.** Lab-level consent is the
  granularity that matches the user model. Per-interaction consent is
  deferred until/unless a regulatory requirement forces it.
- **Cross-tenant comparison views.** The dataset supports it (uniform schema
  across labs) but no cross-tenant route exists yet, by design.
