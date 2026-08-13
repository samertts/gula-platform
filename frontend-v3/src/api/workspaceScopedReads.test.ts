import { describe, expect, it } from "vitest";
import {
  DIRECT_REST_SCOPED_READS_BLOCKED,
  WorkspaceReadBlockedError,
  isPermissionGranted,
  parseVerifiedWorkspaceScope,
  workspaceScopedReads,
} from "./workspaceScopedReads";

describe("بوابة القراءة النطاقية", () => {
  it("تستخرج مختبرًا موثقًا من استجابة سياق التفويض", () => {
    expect(parseVerifiedWorkspaceScope({ user: { lab_id: 24 } })).toEqual({ labId: 24 });
  });

  it("تمنع القراءة عند غياب سياق منشأة موثق", () => {
    expect(() => parseVerifiedWorkspaceScope({ user: { lab_id: null } })).toThrow(WorkspaceReadBlockedError);
  });

  it("تقبل فقط نتيجة سماح صريحة من عقد التفويض", () => {
    expect(isPermissionGranted({ allowed: true })).toBe(true);
    expect(isPermissionGranted({ decision: "deny" })).toBe(false);
    expect(isPermissionGranted({})).toBe(false);
  });

  it("تمنع قراءة REST المباشرة حتى يثبت فرض الصلاحية في الخادم", async () => {
    expect(DIRECT_REST_SCOPED_READS_BLOCKED).toBe(true);

    await expect(workspaceScopedReads.listPatients()).rejects.toMatchObject({
      name: "WorkspaceReadBlockedError",
      reason: "server_enforcement_required",
    });
    await expect(workspaceScopedReads.listOrders()).rejects.toMatchObject({
      name: "WorkspaceReadBlockedError",
      reason: "server_enforcement_required",
    });
  });
});
