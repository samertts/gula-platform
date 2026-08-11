import { describe, expect, it, vi } from "vitest";
import { writeAudit } from "./lis-service";

describe("writeAudit", () => {
  it("appends a complete audit record with the before and after state", async () => {
    const values = vi.fn().mockResolvedValue(undefined);
    const insert = vi.fn().mockReturnValue({ values });
    const beforeState = { status: "draft", version: 1 };
    const afterState = { status: "submitted", version: 2 };

    await writeAudit({ insert }, {
      institutionId: 4,
      actorUserId: 12,
      action: "lab_order.transition",
      entityType: "lab_order",
      entityId: 31,
      outcome: "success",
      beforeState,
      afterState,
    });

    expect(insert).toHaveBeenCalledTimes(1);
    expect(values).toHaveBeenCalledWith(expect.objectContaining({
      institutionId: 4,
      actorUserId: 12,
      action: "lab_order.transition",
      entityType: "lab_order",
      entityId: "31",
      outcome: "success",
      beforeState,
      afterState,
    }));
  });
});
