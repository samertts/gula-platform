/**
 * Centralized Showcase availability control.
 *
 * This is the ONLY module allowed to read the Showcase build-time environment
 * variables (import.meta.env.VITE_DEMO_MODE_* / VITE_SHOWCASE_KILL_SWITCH).
 * Pages and components MUST NOT read those variables directly; they call
 * getShowcaseControl() instead.
 *
 * Evaluation priority (highest wins):
 *   KILL_SWITCH > EXPIRED > DISABLED > ENABLED
 *
 * NOTE ON SCOPE: the current provider is build-time only. A build-time kill
 * switch therefore requires a new build/deployment to take effect; it is NOT
 * an instant remote control. The provider interface exists so a runtime
 * provider can be added later without a redesign.
 *
 * Showcase control affects ONLY the Showcase. It never disables production
 * login, production APIs, NIAM, RBAC, ABAC or Wave A.
 */

export type ShowcaseDisableReason =
  | "kill_switch"
  | "disabled_by_config"
  | "expiry_missing"
  | "expiry_invalid"
  | "expired";

export interface ShowcaseControl {
  enabled: boolean;
  killSwitch: boolean;
  expiresAt: string | null;
  disableReason: ShowcaseDisableReason | null;
  configVersion: string;
  checkedAt: string;
}

/**
 * Abstraction over where Showcase availability comes from. The build-time
 * provider reads VITE_* variables. A future provider may read runtime state.
 */
export interface ShowcaseControlProvider {
  readonly kind: "build-time" | "runtime";
  readonly configVersion: string;
  getControl(now?: Date): ShowcaseControl;
}

export const SHOWCASE_CONTROL_VERSION = "showcase-control-v1";
export const SHOWCASE_KILL_SWITCH_ENV = "VITE_SHOWCASE_KILL_SWITCH";

const TRUE_VALUES = new Set(["true", "1", "yes"]);

export function toBool(raw: string | undefined): boolean {
  return TRUE_VALUES.has(String(raw ?? "").trim().toLowerCase());
}

/** Build-time Showcase control provider. Fail-closed on every invalid state. */
export class BuildTimeShowcaseControlProvider implements ShowcaseControlProvider {
  readonly kind = "build-time" as const;
  readonly configVersion = SHOWCASE_CONTROL_VERSION;

  getControl(now: Date = new Date()): ShowcaseControl {
    const checkedAt = now.toISOString();
    const killSwitch = toBool(import.meta.env.VITE_SHOWCASE_KILL_SWITCH);
    const enabledByEnv = toBool(import.meta.env.VITE_DEMO_MODE_ENABLED);
    const rawExpiry = String(import.meta.env.VITE_DEMO_MODE_EXPIRES_AT ?? "").trim();

    if (killSwitch) {
      return {
        enabled: false,
        killSwitch: true,
        expiresAt: null,
        disableReason: "kill_switch",
        configVersion: this.configVersion,
        checkedAt,
      };
    }

    if (!enabledByEnv) {
      return {
        enabled: false,
        killSwitch: false,
        expiresAt: null,
        disableReason: "disabled_by_config",
        configVersion: this.configVersion,
        checkedAt,
      };
    }

    if (!rawExpiry) {
      return {
        enabled: false,
        killSwitch: false,
        expiresAt: null,
        disableReason: "expiry_missing",
        configVersion: this.configVersion,
        checkedAt,
      };
    }

    const expiresAt = new Date(rawExpiry);
    if (Number.isNaN(expiresAt.getTime())) {
      return {
        enabled: false,
        killSwitch: false,
        expiresAt: null,
        disableReason: "expiry_invalid",
        configVersion: this.configVersion,
        checkedAt,
      };
    }

    if (now.getTime() >= expiresAt.getTime()) {
      return {
        enabled: false,
        killSwitch: false,
        expiresAt: rawExpiry,
        disableReason: "expired",
        configVersion: this.configVersion,
        checkedAt,
      };
    }

    return {
      enabled: true,
      killSwitch: false,
      expiresAt: rawExpiry,
      disableReason: null,
      configVersion: this.configVersion,
      checkedAt,
    };
  }
}

const buildTimeProvider = new BuildTimeShowcaseControlProvider();

/**
 * Evaluated Showcase control for the current time. Call this (do not cache)
 * wherever a decision is made, so that expiry is re-checked on navigation and
 * before rendering protected Showcase routes.
 */
export function getShowcaseControl(now: Date = new Date()): ShowcaseControl {
  return buildTimeProvider.getControl(now);
}

/** ShowcaseControlProvider chosen for this build. */
export const showcaseControlProvider: ShowcaseControlProvider = buildTimeProvider;
