import { describe, expect, it } from "vitest";
import {
  canUsePermissionInWorkspace,
  canUseWorkspace,
  discoverWorkspaces,
  hasPermission,
  permissionCatalog,
  permissionsForRoles,
  orderTransitions,
  resultTransitions,
  sampleTransitions,
} from "../shared/lis-policy";

describe("GULA workspace authorization", () => {
  it("returns only workspaces granted by the account roles", () => {
    expect(discoverWorkspaces(["lab_staff"]).map((workspace) => workspace.id)).toEqual(["laboratory", "radiology"]);
    expect(discoverWorkspaces(["system_admin"]).map((workspace) => workspace.id)).toEqual([
      "clinical",
      "hospital",
      "laboratory",
      "pharmacy",
      "radiology",
      "emergency",
      "public_health",
      "facility",
      "governance",
    ]);
    expect(canUseWorkspace("governance", ["lab_staff"])).toBe(false);
    expect(canUseWorkspace("laboratory", ["lab_staff"])).toBe(true);
  });

  it("does not grant a workspace to an unknown role", () => {
    expect(discoverWorkspaces(["unknown"]).length).toBe(0);
    expect(canUseWorkspace("laboratory", ["unknown"])).toBe(false);
  });
});

describe("GULA role to workspace to permission decisions", () => {
  it("grants laboratory sample permissions only through an authorized workspace", () => {
    expect(hasPermission(["lab_staff"], permissionCatalog.sampleReceive)).toBe(true);
    expect(canUsePermissionInWorkspace("laboratory", ["lab_staff"], permissionCatalog.sampleReceive)).toBe(true);
    expect(canUsePermissionInWorkspace("facility", ["lab_staff"], permissionCatalog.sampleReceive)).toBe(false);
  });

  it("keeps patient access read-only and scoped", () => {
    expect(permissionsForRoles(["patient"])).toContain(permissionCatalog.resultRead);
    expect(permissionsForRoles(["patient"])).not.toContain(permissionCatalog.resultRelease);
    expect(canUsePermissionInWorkspace("laboratory", ["patient"], permissionCatalog.sampleReceive)).toBe(false);
  });

  it("does not allow unknown roles to inherit permissions", () => {
    expect(permissionsForRoles(["unknown"])).toEqual([]);
    expect(canUsePermissionInWorkspace("governance", ["unknown"], permissionCatalog.auditRead)).toBe(false);
  });
});

describe("GULA clinical state machines", () => {
  it("keeps order progression explicit and terminal states closed", () => {
    expect(orderTransitions.draft).toContain("submitted");
    expect(orderTransitions.in_progress).toEqual(["result_pending_review", "cancelled"]);
    expect(orderTransitions.completed).toEqual([]);
    expect(orderTransitions.cancelled).toEqual([]);
  });

  it("requires verified samples before processing", () => {
    expect(sampleTransitions.expected).toEqual(["received", "rejected"]);
    expect(sampleTransitions.received).toContain("verified");
    expect(sampleTransitions.verified).toEqual(["processing"]);
    expect(sampleTransitions.rejected).toEqual([]);
  });

  it("requires review before result release", () => {
    expect(resultTransitions.not_started).toEqual(["entered"]);
    expect(resultTransitions.entered).toContain("pending_review");
    expect(resultTransitions.pending_review).toEqual(["approved", "rejected"]);
    expect(resultTransitions.approved).toEqual(["released"]);
    expect(resultTransitions.released).toEqual([]);
  });
});
