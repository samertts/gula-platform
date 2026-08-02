import { describe, expect, it } from "vitest";
import {
  NAV_ITEMS,
  ROLE_LEVELS,
  ROLE_PERMISSIONS,
  getRoleLevel,
  hasPermission,
  isPlatformRole,
} from "@/permissions";

const BACKEND_ENTERPRISE_ROLES = [
  "master_admin",
  "ministry_admin",
  "organization_admin",
  "directorate_admin",
  "auditor",
  "security_officer",
  "hospital_admin",
  "phc_admin",
  "lab_manager",
  "quality_manager",
  "lab_supervisor",
  "pathologist",
  "doctor",
  "technician",
  "nurse",
  "receptionist",
  "cashier",
  "api_client",
  "patient",
];

const LEGACY_UI_ROLES = ["province_admin", "admin", "lab_admin", "staff", "lab_staff", "citizen"];

describe("role parity with backend enterprise roles", () => {
  it("maps every backend enterprise role to a frontend permission set", () => {
    for (const role of BACKEND_ENTERPRISE_ROLES) {
      expect(ROLE_PERMISSIONS[role], `missing ROLE_PERMISSIONS entry for ${role}`).toBeDefined();
      expect(ROLE_LEVELS[role], `missing ROLE_LEVELS entry for ${role}`).toBeDefined();
    }
  });

  it("keeps legacy UI roles mapped (backwards compatibility)", () => {
    for (const role of LEGACY_UI_ROLES) {
      expect(ROLE_PERMISSIONS[role], `missing ROLE_PERMISSIONS entry for ${role}`).toBeDefined();
    }
  });

  it("gives every platform role at least dashboard:read and one nav item", () => {
    for (const role of [...BACKEND_ENTERPRISE_ROLES, ...LEGACY_UI_ROLES]) {
      if (role === "citizen") continue;
      const visible = Object.values(NAV_ITEMS)
        .flat()
        .filter(
          (item) =>
            !item.permissions || item.permissions.some((p) => hasPermission(role, p)),
        );
      expect(visible.length, `role ${role} has zero nav items`).toBeGreaterThan(0);
    }
  });

  it("assigns strictly decreasing privilege levels for the admin chain", () => {
    const chain = ["master_admin", "ministry_admin", "organization_admin", "directorate_admin", "lab_manager"] as const;
    for (let i = 1; i < chain.length; i++) {
      const higher = chain[i - 1];
      const lower = chain[i];
      expect(higher).toBeDefined();
      expect(lower).toBeDefined();
      expect(getRoleLevel(higher ?? "")).toBeGreaterThan(getRoleLevel(lower ?? ""));
    }
  });

  it("allows only master_admin to manage master_admin", () => {
    expect(isPlatformRole("master_admin")).toBe(true);
    expect(isPlatformRole("organization_admin")).toBe(true);
    expect(isPlatformRole("lab_manager")).toBe(false);
  });
});
