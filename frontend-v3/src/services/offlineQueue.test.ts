import { describe, expect, it } from "vitest";
import { MAX_QUEUE_SIZE } from "./offlineQueue";

describe("offline queue capacity contract", () => {
  it("keeps the emergency queue cap and operator-facing failure contract stable", () => {
    expect(MAX_QUEUE_SIZE).toBe(5000);
    expect("Offline queue is full; use the institution fallback procedure").toContain("Offline queue is full");
  });
});
