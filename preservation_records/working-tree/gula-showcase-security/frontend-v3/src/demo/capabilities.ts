/**
 * Showcase persona / capability isolation.
 *
 * Showcase personas are presentation-only previews. They are NOT production
 * authorization roles: a SHOWCASE health_admin is never a PRODUCTION admin.
 * Personas only grant read-only, synthetic-viewing capabilities. There are no
 * mutation capabilities anywhere in the Showcase.
 *
 * Production authorization (RoleGuard, ROLE_PERMISSIONS, ABAC/RBAC) is never
 * consulted for a Showcase persona, and Showcase code never imports it.
 */

import type { DemoProfileId } from "./profiles";

export const SHOWCASE_CAPABILITIES = [
  "view_dashboard",
  "view_demo_patient",
  "view_demo_lab",
  "view_demo_results",
  "view_demo_statistics",
  "view_demo_appointments",
] as const;

export type ShowcaseCapability = (typeof SHOWCASE_CAPABILITIES)[number];

/** Capabilities that must NEVER exist in the Showcase. */
export const DENIED_SHOWCASE_CAPABILITIES = [
  "create",
  "update",
  "delete",
  "approve",
  "reject",
  "authorize",
  "prescribe",
  "dispense",
  "manage_users",
  "manage_permissions",
  "manage_organizations",
  "manage_facilities",
  "modify_patient",
  "modify_result",
  "modify_clinical_record",
] as const;

export type DeniedShowcaseCapability = (typeof DENIED_SHOWCASE_CAPABILITIES)[number];

/**
 * View-only capability sets per persona. These are capabilities of the
 * presentation surface only — never production permissions.
 */
export const PERSONA_CAPABILITIES: Record<DemoProfileId, readonly ShowcaseCapability[]> = {
  citizen: ["view_dashboard", "view_demo_appointments"],
  doctor: ["view_dashboard", "view_demo_patient", "view_demo_results", "view_demo_appointments"],
  lab_staff: ["view_dashboard", "view_demo_lab", "view_demo_results"],
  nurse: ["view_dashboard", "view_demo_patient"],
  health_admin: ["view_dashboard", "view_demo_statistics"],
};

export function hasShowcaseCapability(persona: DemoProfileId, capability: string): boolean {
  if (!isShowcaseCapability(capability)) return false;
  return (PERSONA_CAPABILITIES[persona] ?? []).includes(capability);
}

export function isShowcaseCapability(value: string): value is ShowcaseCapability {
  return (SHOWCASE_CAPABILITIES as readonly string[]).includes(value);
}

export function isDeniedShowcaseCapability(value: string): value is DeniedShowcaseCapability {
  return (DENIED_SHOWCASE_CAPABILITIES as readonly string[]).includes(value);
}

export function personaCapabilities(persona: DemoProfileId): readonly ShowcaseCapability[] {
  return PERSONA_CAPABILITIES[persona] ?? [];
}
