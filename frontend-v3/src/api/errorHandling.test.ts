import axios from "axios";
import { describe, expect, it } from "vitest";
import { authFailureMessage, classifyApiError } from "./errorHandling";

describe("identity error UX", () => {
  it("maps unauthorized to reauthentication without enumeration", () => {
    const info = authFailureMessage({ response: { status: 401, data: { detail: "Invalid email or password" } } });
    expect(info.code).toBe("INVALID_CREDENTIALS");
    expect(info.message).not.toContain("email");
  });
  it("maps forbidden and conflict to safe contextual messages", () => {
    expect(classifyApiError({ response: { status: 403 } }).kind).toBe("FORBIDDEN");
    expect(classifyApiError({ response: { status: 409 } }).kind).toBe("CONFLICT");
  });
  it("maps rate limits and server failures to retryable UX", () => {
    expect(classifyApiError({ response: { status: 429, headers: { "retry-after": "10" } } }).retryable).toBe(true);
    expect(classifyApiError({ response: { status: 503 } }).kind).toBe("SERVER_UNAVAILABLE");
  });
  it("maps network failures to offline without stale-data fallback", () => {
    const error = new axios.AxiosError("Network Error", "ERR_NETWORK", undefined, undefined, undefined);
    expect(classifyApiError(error).kind).toBe("OFFLINE");
  });
});
