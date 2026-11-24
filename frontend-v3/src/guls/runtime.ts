import { getLanguage, gulsRegistry, type LanguageDefinition, type WritingDirection } from './registry';

export interface Resolution {
  requested: string | null;
  selected: string;
  fallbackUsed: boolean;
  direction: WritingDirection;
  localeTag: string | null;
  reason: 'requested_ready' | 'preferred_ready' | 'mandatory_fallback';
}

export interface StableMessage {
  code: string;
  parameters: Record<string, unknown>;
  correlationId?: string;
}

export interface TranslationResult {
  text: string;
  missing: boolean;
  fallbackUsed: boolean;
}

const TRANSLATION_KEY = /^(ui|action|label|message|error|clinical)\.[a-z0-9_]+(?:\.[a-z0-9_-]+){0,4}$/;
const STABLE_CODE = /^[A-Z][A-Z0-9_]{2,63}$/;

const DIGIT_MAPS: Record<string, string> = {
  ar: '٠١٢٣٤٥٦٧٨٩',
  ckb: '٠١٢٣٤٥٦٧٨٩',
  fa: '۰۱۲۳۴۵۶۷۸۹',
  ur: '۰۱۲۳۴۵۶۷۸۹',
};

function localizeDigits(value: string, languageId: string): string {
  const map = DIGIT_MAPS[languageId];
  if (!map) return value;
  return value.replace(/[0-9]/g, (digit) => map[Number(digit)] ?? digit);
}

export function resolveLanguage(
  requested: string | null | undefined,
  readyLanguageIds: ReadonlySet<string>,
  preferred?: string | null,
): Resolution {
  const fallback = getLanguage(gulsRegistry.fallbackLanguage);
  if (!fallback || !fallback.is_active) {
    throw new Error('English fallback is required');
  }
  const requestedDefinition = getLanguage(requested);
  if (requestedDefinition && requestedDefinition.is_active && readyLanguageIds.has(requestedDefinition.language_id)) {
    return {
      requested: requested ?? null,
      selected: requestedDefinition.language_id,
      fallbackUsed: false,
      direction: requestedDefinition.direction ?? 'ltr',
      localeTag: requestedDefinition.locale_tag,
      reason: 'requested_ready',
    };
  }
  const preferredDefinition = getLanguage(preferred);
  if (preferredDefinition && preferredDefinition.is_active && readyLanguageIds.has(preferredDefinition.language_id)) {
    return {
      requested: requested ?? null,
      selected: preferredDefinition.language_id,
      fallbackUsed: true,
      direction: preferredDefinition.direction ?? 'ltr',
      localeTag: preferredDefinition.locale_tag,
      reason: 'preferred_ready',
    };
  }
  if (!readyLanguageIds.has(fallback.language_id)) {
    throw new Error('No usable language including English fallback');
  }
  return {
    requested: requested ?? null,
    selected: fallback.language_id,
    fallbackUsed: true,
    direction: fallback.direction ?? 'ltr',
    localeTag: fallback.locale_tag,
    reason: 'mandatory_fallback',
  };
}

export function directionFor(languageId: string): WritingDirection {
  const definition: LanguageDefinition | undefined = getLanguage(languageId);
  return definition?.is_active && definition.direction ? definition.direction : 'ltr';
}

export function translateKey(
  catalog: Readonly<Record<string, string>>,
  fallbackCatalog: Readonly<Record<string, string>>,
  key: string,
  parameters: Record<string, string | number> = {},
): TranslationResult {
  if (!TRANSLATION_KEY.test(key)) {
    return { text: '', missing: true, fallbackUsed: false };
  }
  let template = catalog[key];
  let fallbackUsed = false;
  if (!template) {
    template = fallbackCatalog[key];
    fallbackUsed = true;
  }
  if (template === undefined) {
    return { text: '', missing: true, fallbackUsed: false };
  }
  let text = template;
  for (const [name, value] of Object.entries(parameters)) {
    text = text.replaceAll(`{${name}}`, String(value));
  }
  return { text, missing: false, fallbackUsed };
}

export function formatNumber(value: string | number, languageId: string): string {
  const text = typeof value === 'number' ? value.toString() : value;
  return localizeDigits(text, languageId);
}

export function formatIdentifier(value: string): string {
  return value;
}

export function stableMessage(code: string, parameters: Record<string, unknown> = {}, correlationId?: string): StableMessage {
  if (!STABLE_CODE.test(code)) {
    throw new Error('Invalid stable error code');
  }
  return { code, parameters, ...(correlationId ? { correlationId } : {}) };
}
