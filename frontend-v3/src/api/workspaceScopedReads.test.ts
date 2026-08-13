import { describe, expect, it } from "vitest";
import {
  WorkspaceReadBlockedError,
  isPermissionGranted,
  parseVerifiedWorkspaceScope,
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
});
