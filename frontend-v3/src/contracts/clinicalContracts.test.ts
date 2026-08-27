import { describe, expect, it } from "vitest";
import { CLINICAL_CONTRACTS, isAllowedTransition, requireAllowedTransition, requiresClinicalWriteControls } from "./clinicalContracts";

describe("clinicalContracts", () => {
  it("يطبق الانتقالات الرسمية ويمنع التعديل الصامت بعد SIGNED", () => {
    expect(isAllowedTransition("appointment", "REQUESTED", "CONFIRMED")).toBe(true);
    expect(isAllowedTransition("appointment", "CONFIRMED", "CHECKED_IN")).toBe(true);
    expect(isAllowedTransition("encounter", "COMPLETED", "SIGNED")).toBe(true);
    expect(isAllowedTransition("encounter", "SIGNED", "IN_PROGRESS")).toBe(false);
    expect(isAllowedTransition("result", "RELEASED", "DRAFT")).toBe(false);
    expect(() => requireAllowedTransition("encounter", "SIGNED", "IN_PROGRESS")).toThrow("INVALID_STATE_TRANSITION");
  });

  it("يثبت أن المجالات الحساسة تحتاج authorization/audit/idempotency/concurrency", () => {
    for (const [contractId, contract] of Object.entries(CLINICAL_CONTRACTS)) {
      expect(requiresClinicalWriteControls(contractId as keyof typeof CLINICAL_CONTRACTS)).toEqual(contract.writeSafety);
    }
    expect(CLINICAL_CONTRACTS.result.writeSafety.requiresAudit).toBe(true);
    expect(CLINICAL_CONTRACTS.result.writeSafety.requiresIdempotency).toBe(true);
    expect(CLINICAL_CONTRACTS.result.writeSafety.requiresConcurrency).toBe(true);
  });
});
