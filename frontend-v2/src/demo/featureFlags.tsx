import React, { createContext, useContext, useState, useCallback } from 'react';

export interface FeatureFlags {
  ai: boolean;
  ocr: boolean;
  fhir: boolean;
  notifications: boolean;
  analytics: boolean;
  knowledgeGraph: boolean;
  experimental: boolean;
  governmentModule: boolean;
  laboratoryModule: boolean;
}

interface FeatureFlagState {
  flags: FeatureFlags;
  setFlag: (key: keyof FeatureFlags, value: boolean) => void;
  toggleFlag: (key: keyof FeatureFlags) => void;
  resetFlags: () => void;
  isFeatureEnabled: (key: keyof FeatureFlags) => boolean;
}

const defaultFlags: FeatureFlags = {
  ai: import.meta.env.VITE_FEATURE_AI !== 'false',
  ocr: import.meta.env.VITE_FEATURE_OCR !== 'false',
  fhir: import.meta.env.VITE_FEATURE_FHIR !== 'false',
  notifications: import.meta.env.VITE_FEATURE_NOTIFICATIONS !== 'false',
  analytics: import.meta.env.VITE_FEATURE_ANALYTICS !== 'false',
  knowledgeGraph: import.meta.env.VITE_FEATURE_KNOWLEDGE_GRAPH !== 'false',
  experimental: import.meta.env.VITE_FEATURE_EXPERIMENTAL === 'true',
  governmentModule: true,
  laboratoryModule: true,
};

const FeatureFlagContext = createContext<FeatureFlagState | null>(null);

export function FeatureFlagProvider({ children }: { children: React.ReactNode }) {
  const [flags, setFlags] = useState<FeatureFlags>(() => {
    const stored = localStorage.getItem('gula_feature_flags');
    if (stored) {
      try {
        return { ...defaultFlags, ...JSON.parse(stored) };
      } catch {
        localStorage.removeItem('gula_feature_flags');
      }
    }
    return { ...defaultFlags };
  });

  const persistFlags = useCallback((newFlags: FeatureFlags) => {
    localStorage.setItem('gula_feature_flags', JSON.stringify(newFlags));
  }, []);

  const setFlag = useCallback((key: keyof FeatureFlags, value: boolean) => {
    setFlags(prev => {
      const next = { ...prev, [key]: value };
      persistFlags(next);
      return next;
    });
  }, [persistFlags]);

  const toggleFlag = useCallback((key: keyof FeatureFlags) => {
    setFlags(prev => {
      const next = { ...prev, [key]: !prev[key] };
      persistFlags(next);
      return next;
    });
  }, [persistFlags]);

  const resetFlags = useCallback(() => {
    setFlags({ ...defaultFlags });
    persistFlags(defaultFlags);
  }, [persistFlags]);

  const isFeatureEnabled = useCallback((key: keyof FeatureFlags): boolean => {
    return flags[key];
  }, [flags]);

  return (
    <FeatureFlagContext.Provider
      value={{ flags, setFlag, toggleFlag, resetFlags, isFeatureEnabled }}
    >
      {children}
    </FeatureFlagContext.Provider>
  );
}

export function useFeatureFlag(): FeatureFlagState {
  const context = useContext(FeatureFlagContext);
  if (!context) {
    throw new Error('useFeatureFlag must be used within FeatureFlagProvider');
  }
  return context;
}
