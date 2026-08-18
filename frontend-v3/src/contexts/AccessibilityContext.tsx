import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { userPreferencesApi } from "@/api/endpoints";
import type { AccessibilityPreferences, AccessibilityResponse } from "@/types";

const DEFAULT_PREFERENCES: AccessibilityPreferences = {
  language: "ar",
  font_size: "medium",
  text_scale: 1,
  high_contrast: false,
  color_blind_mode: "none",
  reduced_color_dependence: true,
  screen_reader_optimized: false,
  reduced_motion: false,
  captions: true,
  text_alternatives: true,
  visual_alerts: true,
  transcripts: true,
  mute_safe_notifications: true,
  larger_touch_targets: false,
  reduced_interaction_complexity: false,
  longer_timeout: false,
  keyboard_navigation: true,
  voice_interaction: false,
  dyslexia_friendly: false,
  simplified_interface: false,
  reduced_visual_density: false,
  clear_language: false,
  step_by_step_workflows: false,
  reduced_notifications: false,
  disable_flashing: true,
  static_alternatives: true,
};

interface AccessibilityContextValue {
  preferences: AccessibilityPreferences;
  version: number;
  isLoading: boolean;
  isSaving: boolean;
  saveError: string | null;
  update: (patch: Partial<AccessibilityPreferences>) => Promise<void>;
  preview: (patch: Partial<AccessibilityPreferences>) => void;
  clearPreview: () => void;
  reload: () => Promise<void>;
}

const AccessibilityContext = createContext<AccessibilityContextValue | null>(null);

function applyPreferences(preferences: AccessibilityPreferences) {
  const root = document.documentElement;
  root.dataset.colorBlindMode = preferences.color_blind_mode;
  root.dataset.screenReaderOptimized = String(preferences.screen_reader_optimized);
  root.dataset.reducedColorDependence = String(preferences.reduced_color_dependence);
  root.dataset.reducedVisualDensity = String(preferences.reduced_visual_density);
  root.style.setProperty("--gula-text-scale", String(preferences.text_scale));
  root.style.setProperty("--gula-touch-scale", preferences.larger_touch_targets ? "1.15" : "1");
  root.classList.toggle("gula-high-contrast", preferences.high_contrast);
  root.classList.toggle("gula-reduced-motion", preferences.reduced_motion || preferences.disable_flashing);
  root.classList.toggle("gula-dyslexia-friendly", preferences.dyslexia_friendly);
  root.classList.toggle("gula-simple-interface", preferences.simplified_interface);
}

export function AccessibilityProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading: authLoading, demoMode } = useAuth();
  const [preferences, setPreferences] = useState<AccessibilityPreferences>(DEFAULT_PREFERENCES);
  const [version, setVersion] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!isAuthenticated || demoMode) return;
    setIsLoading(true);
    try {
      const response: AccessibilityResponse = await userPreferencesApi.getAccessibility();
      setPreferences({ ...DEFAULT_PREFERENCES, ...response });
      setVersion(response.version);
      setSaveError(null);
    } catch {
      // Accessibility must remain usable locally even when the API is unavailable.
      setPreferences(DEFAULT_PREFERENCES);
      setVersion(0);
    } finally {
      setIsLoading(false);
    }
  }, [demoMode, isAuthenticated]);

  useEffect(() => {
    if (!authLoading) void reload();
  }, [authLoading, reload]);

  useEffect(() => {
    applyPreferences(preferences);
    return () => {
      document.documentElement.style.removeProperty("--gula-text-scale");
      document.documentElement.style.removeProperty("--gula-touch-scale");
    };
  }, [preferences]);

  const preview = useCallback((patch: Partial<AccessibilityPreferences>) => {
    applyPreferences({ ...preferences, ...patch });
  }, [preferences]);

  const clearPreview = useCallback(() => {
    applyPreferences(preferences);
  }, [preferences]);

  const update = useCallback(async (patch: Partial<AccessibilityPreferences>) => {
    const next = { ...preferences, ...patch };
    setIsSaving(true);
    setSaveError(null);
    try {
      const response = await userPreferencesApi.updateAccessibility({ ...next, ...(version ? { version } : {}) });
      setPreferences({ ...DEFAULT_PREFERENCES, ...response });
      setVersion(response.version);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "تعذر حفظ تفضيلات الوصول");
      throw error;
    } finally {
      setIsSaving(false);
    }
  }, [preferences, version]);

  const value = useMemo(
    () => ({ preferences, version, isLoading, isSaving, saveError, update, preview, clearPreview, reload }),
    [clearPreview, isLoading, isSaving, preferences, preview, reload, saveError, update, version],
  );

  return <AccessibilityContext.Provider value={value}>{children}</AccessibilityContext.Provider>;
}

export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (!context) throw new Error("useAccessibility must be used within AccessibilityProvider");
  return context;
}

export { DEFAULT_PREFERENCES };
