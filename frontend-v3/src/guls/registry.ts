import sharedRegistry from '../../../shared/guls/language_registry.json';

export type WritingDirection = 'ltr' | 'rtl';
export type LanguageClassification = 'core' | 'downloadable';

export interface LanguageDefinition {
  language_id: string;
  locale_tag: string | null;
  native_name: string | null;
  english_name: string;
  direction: WritingDirection | null;
  script: string | null;
  region: string | null;
  classification: LanguageClassification;
  is_active: boolean;
  is_publishable: boolean;
  approval_status: string;
  pack_version: string;
  translation_coverage: number;
}

interface SharedRegistryPayload {
  fallback_language: string;
  languages: LanguageDefinition[];
}

const payload = sharedRegistry as SharedRegistryPayload;

export const gulsRegistry = {
  fallbackLanguage: payload.fallback_language,
  languages: payload.languages,
};

export function getLanguage(identifier: string | null | undefined): LanguageDefinition | undefined {
  if (!identifier) return undefined;
  const direct = gulsRegistry.languages.find((item) => item.language_id === identifier);
  if (direct) return direct;
  const lowered = identifier.toLowerCase();
  return gulsRegistry.languages.find((item) => item.locale_tag?.toLowerCase() === lowered);
}

export function coreLanguages(): LanguageDefinition[] {
  return gulsRegistry.languages.filter((item) => item.classification === 'core');
}

export function activeLanguages(): LanguageDefinition[] {
  return gulsRegistry.languages.filter((item) => item.is_active);
}
