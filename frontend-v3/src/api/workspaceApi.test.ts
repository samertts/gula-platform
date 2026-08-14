import { describe, expect, it } from "vitest";
import {
  OperationalReadBlockedError,
  OperationalWriteBlockedError,
  assertFrontendReadIsAllowed,
  assertFrontendWriteIsAllowed,
} from "./client";

describe("workspace API contract gates", () => {
  it("allows backend workspace discovery and detail reads", () => {
    expect(() => assertFrontendReadIsAllowed("get", "/niam/workspaces")).not.toThrow();
    expect(() => assertFrontendReadIsAllowed("get", "/niam/workspaces/abc")).not.toThrow();
  });

  it("allows only server-authoritative workspace switching", () => {
    expect(() => assertFrontendWriteIsAllowed("post", "/niam/workspaces/abc/switch")).not.toThrow();
    expect(() => assertFrontendWriteIsAllowed("patch", "/niam/workspaces/abc")).toThrow(OperationalWriteBlockedError);
    expect(() => assertFrontendWriteIsAllowed("delete", "/niam/workspaces/abc")).toThrow(OperationalWriteBlockedError);
  });

  it("continues to block direct clinical reads", () => {
    expect(() => assertFrontendReadIsAllowed("get", "/patients")).toThrow(OperationalReadBlockedError);
    expect(() => assertFrontendReadIsAllowed("get", "/lims/orders")).toThrow(OperationalReadBlockedError);
  });
});
