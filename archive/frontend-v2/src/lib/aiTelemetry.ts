/**
 * AI interaction telemetry helpers — Phase 3 + Phase 4 client.
 *
 * These post to the backend's flag-gated routes:
 *   POST /api/ai/interactions
 *   POST /api/ai/feedback
 *   POST /api/ai/unresolved
 *
 * All requests go through the same-origin ``/api/`` rewrite that Vercel
 * already proxies to ``api.gula-platform.org`` (see repo-root ``vercel.json``).
 * That means cookies/JWT propagate naturally and CORS is not a concern in
 * production.
 *
 * Failure mode
 * ------------
 * Every helper resolves to ``{ ok: false, reason }`` on failure — telemetry
 * must NEVER crash the UI. Callers should fire-and-forget.
 */
import { getAnonymousSessionId, track, captureError } from './telemetry';

const API_BASE = ((import.meta as any).env?.VITE_API_BASE || '/api').replace(/\/$/, '');

export type AIFeedbackSignal =
  | 'helpful'
  | 'not_helpful'
  | 'unclear'
  | 'need_doctor'
  | 'incorrect_interpretation';

export type AIIntent =
  | 'interpret_result'
  | 'explain_biomarker'
  | 'navigate'
  | 'educational'
  | 'decision_support'
  | 'unknown';

export interface RetrievalRef {
  source?:     string;
  doc_id?:     string;
  doc_title?:  string;
  chunk_text?: string;
  similarity?: number;
  rank?:       number;
}

export interface LogInteractionInput {
  language?:           string;
  region?:             string;
  intent?:             AIIntent | string;
  prompt?:             string;
  prompt_redacted?:    boolean;
  response?:           string;
  response_model?:     string;
  retrieval_strategy?: string;
  retrieval_refs?:     RetrievalRef[];
  biomarkers?:         string[];
  latency_ms?:         number;
  status?:             'ok' | 'error' | 'guardrail_blocked' | 'escalated';
  error_code?:         string;
}

export interface LogInteractionResult {
  ok: true;
  id: string;
  created_at: string;
}
export interface TelemetryFailure {
  ok: false;
  reason: string;
  status?: number;
}

async function _postJson(path: string, body: unknown): Promise<Response> {
  return fetch(`${API_BASE}${path}`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

/** POST /api/ai/interactions */
export async function logInteraction(
  input: LogInteractionInput,
): Promise<LogInteractionResult | TelemetryFailure> {
  const anon = getAnonymousSessionId();
  try {
    const res = await _postJson('/ai/interactions', {
      anonymous_session_id: anon,
      ...input,
    });
    if (!res.ok) {
      // 503 with AI_DATASET_DISABLED is the normal pre-launch state — don't
      // alarm the user, just record locally for analytics counters.
      if (res.status === 503) {
        track('ai.dataset.disabled', { status: res.status });
        return { ok: false, reason: 'dataset_disabled', status: res.status };
      }
      track('ai.interaction.log_failed', { status: res.status });
      return { ok: false, reason: 'http_error', status: res.status };
    }
    const json = await res.json();
    track('ai.interaction.logged', {
      intent: input.intent,
      language: input.language,
      retrieval_count: input.retrieval_refs?.length ?? 0,
      latency_ms: input.latency_ms,
    });
    return { ok: true, id: json.id, created_at: json.created_at };
  } catch (e: any) {
    captureError(e, { where: 'aiTelemetry.logInteraction' });
    return { ok: false, reason: 'network_error' };
  }
}

/** POST /api/ai/feedback */
export async function submitFeedback(
  interactionId: string,
  signal: AIFeedbackSignal,
  notes?: string,
): Promise<{ ok: true; id: string } | TelemetryFailure> {
  try {
    const res = await _postJson('/ai/feedback', {
      interaction_id: interactionId,
      anonymous_session_id: getAnonymousSessionId(),
      signal,
      notes,
    });
    if (!res.ok) {
      if (res.status === 503) {
        return { ok: false, reason: 'feedback_disabled', status: res.status };
      }
      return { ok: false, reason: 'http_error', status: res.status };
    }
    const json = await res.json();
    track('ai.feedback.submitted', { signal });
    return { ok: true, id: json.id };
  } catch (e: any) {
    captureError(e, { where: 'aiTelemetry.submitFeedback' });
    return { ok: false, reason: 'network_error' };
  }
}

/** POST /api/ai/unresolved */
export async function logUnresolved(
  question: string,
  opts?: { interactionId?: string; language?: string; category?: string },
): Promise<{ ok: true; id: string } | TelemetryFailure> {
  try {
    const res = await _postJson('/ai/unresolved', {
      interaction_id: opts?.interactionId,
      anonymous_session_id: getAnonymousSessionId(),
      question,
      language: opts?.language,
      category: opts?.category,
    });
    if (!res.ok) {
      if (res.status === 503) {
        return { ok: false, reason: 'dataset_disabled', status: res.status };
      }
      return { ok: false, reason: 'http_error', status: res.status };
    }
    const json = await res.json();
    track('ai.unresolved.logged', { category: opts?.category });
    return { ok: true, id: json.id };
  } catch (e: any) {
    captureError(e, { where: 'aiTelemetry.logUnresolved' });
    return { ok: false, reason: 'network_error' };
  }
}
