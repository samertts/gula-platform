export interface ApiResponse<T = unknown> {
  data?: T;
  message?: string;
  message_ar?: string;
  error?: string;
  detail?: string | { message: string; message_ar: string };
  request_id?: string;
}

export interface PaginatedResponse<T> {
  total: number;
  skip: number;
  limit: number;
  items?: T[];
  results?: T[];
  data?: T[];
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: UserInfo;
  demo_mode?: boolean;
}

export interface UserInfo {
  id: number;
  name: string;
  email: string;
  role: string;
  lab_id: number | null;
  lab_name: string | null;
  is_verified?: boolean;
}

export interface JwtPayload {
  user_id: number;
  lab_id: number | null;
  role: string;
  perm_ver: number;
  type: string;
  jti: string;
  exp: number;
}


export type AccessibilityLanguage = "ar-IQ" | "ar" | "en" | "ku" | "tk" | "syr" | "fa";
export type AccessibilityFontSize = "small" | "medium" | "large" | "x-large";
export type ColorBlindMode = "none" | "protanopia" | "deuteranopia" | "tritanopia" | "monochrome";

export interface AccessibilityPreferences {
  language: AccessibilityLanguage;
  font_size: AccessibilityFontSize;
  text_scale: number;
  high_contrast: boolean;
  color_blind_mode: ColorBlindMode;
  reduced_color_dependence: boolean;
  screen_reader_optimized: boolean;
  reduced_motion: boolean;
  captions: boolean;
  text_alternatives: boolean;
  visual_alerts: boolean;
  transcripts: boolean;
  mute_safe_notifications: boolean;
  larger_touch_targets: boolean;
  reduced_interaction_complexity: boolean;
  longer_timeout: boolean;
  keyboard_navigation: boolean;
  voice_interaction: boolean;
  dyslexia_friendly: boolean;
  simplified_interface: boolean;
  reduced_visual_density: boolean;
  clear_language: boolean;
  step_by_step_workflows: boolean;
  reduced_notifications: boolean;
  disable_flashing: boolean;
  static_alternatives: boolean;
}

export interface AccessibilityResponse extends AccessibilityPreferences {
  version: number;
  status: "saved" | "default";
}

export interface HealthPreferencesPayload {
  allergies: string[];
  chronic_conditions: string[];
  communication_needs: string | null;
  emergency_assistance_preferences: string | null;
  other_health_considerations: string | null;
}

export interface HealthPreferencesResponse {
  status: "saved" | "consent_required" | "empty";
  consent_granted: boolean;
  consent_version?: string | null;
  version?: number | null;
  preferences?: HealthPreferencesPayload | null;
}
