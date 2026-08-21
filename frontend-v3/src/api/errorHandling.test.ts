import axios from "axios";
import { describe, expect, it } from "vitest";
import { authFailureMessage, classifyApiError } from "./errorHandling";

describe("identity error UX", () => {
  it("maps unauthorized to reauthentication without enumeration", () => {
    const info = authFailureMessage({ response: { status: 401, data: { detail: "Invalid email or password" } } });
    expect(info.code).toBe("INVALID_CREDENTIALS");
    expect(info.message).not.toContain("email");
  });
  it("maps unauthorized, verification, forbidden, and conflict without leaking details", () => {
    expect(classifyApiError({ response: { status: 401 } }).reauthenticate).toBe(true);
    const verification = classifyApiError({ response: { status: 403, data: { detail: { code: "VERIFICATION_REQUIRED" } } } });
    expect(verification.kind).toBe("FORBIDDEN");
    expect(verification.message).toContain("التحقق");
    expect(classifyApiError({ response: { status: 403 } }).message).not.toContain("account");
    const conflict = classifyApiError({ response: { status: 409 } });
    expect(conflict.kind).toBe("CONFLICT");
    expect(conflict.retryable).toBe(true);
  });
  it("maps rate limits and server failures to retryable UX with backoff evidence", () => {
    const limited = classifyApiError({ response: { status: 429, headers: { "retry-after": "10" } } });
    expect(limited.retryable).toBe(true);
    expect(limited.retryAfterSeconds).toBe(10);
    const unavailable = classifyApiError({ response: { status: 503 } });
    expect(unavailable.kind).toBe("SERVER_UNAVAILABLE");
    expect(unavailable.retryable).toBe(true);
  });

  it("keeps validation errors server-derived and non-retryable", () => {
    const info = classifyApiError({ response: { status: 422, data: { detail: { code: "INVALID_CONTEXT", message_ar: "بيانات غير صالحة" } } } });
    expect(info.kind).toBe("VALIDATION");
    expect(info.code).toBe("INVALID_CONTEXT");
    expect(info.message).toBe("بيانات غير صالحة");
    expect(info.retryable).toBeUndefined();
  });
  it("maps network failures to offline without stale-data fallback", () => {
    const error = new axios.AxiosError("Network Error", "ERR_NETWORK", undefined, undefined, undefined);
    expect(classifyApiError(error).kind).toBe("OFFLINE");
  });
});
