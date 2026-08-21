import axios from "axios";
import type { AuthStateError } from "@/auth/authState";

export type ApiErrorKind =
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "CONFLICT"
  | "RATE_LIMITED"
  | "SERVER_UNAVAILABLE"
  | "OFFLINE"
  | "VALIDATION"
  | "UNKNOWN";

export interface ApiErrorInfo extends AuthStateError {
  kind: ApiErrorKind;
  status?: number;
  retryAfterSeconds?: number;
}

function hasResponse(error: unknown): error is { response?: { status?: number; data?: { detail?: unknown }; headers?: Record<string, unknown> }; request?: unknown; code?: string; message?: string } {
  return axios.isAxiosError(error) || Boolean(error && typeof error === "object" && "response" in error);
}

function statusOf(error: unknown): number | undefined {
  if (hasResponse(error)) return error.response?.status;
  return undefined;
}

function detailOf(error: unknown): { code?: string; message?: string; message_ar?: string } {
  if (!hasResponse(error)) return {};
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return { message: detail };
  if (detail && typeof detail === "object") {
    const objectDetail = detail as Record<string, unknown>;
    return {
      code: typeof objectDetail.code === "string" ? objectDetail.code : undefined,
      message: typeof objectDetail.message === "string" ? objectDetail.message : undefined,
      message_ar: typeof objectDetail.message_ar === "string" ? objectDetail.message_ar : undefined,
    };
  }
  return {};
}

export function classifyApiError(error: unknown, fallback = "تعذر إكمال العملية."): ApiErrorInfo {
  const status = statusOf(error);
  const detail = detailOf(error);
  const offline = typeof navigator !== "undefined" && !navigator.onLine;
  const networkFailure = hasResponse(error) && !error.response && (Boolean(error.request) || error.code === "ERR_NETWORK" || error.message === "Network Error");
  if (offline || networkFailure) {
    return {
      kind: "OFFLINE",
      code: "OFFLINE",
      message: "لا يوجد اتصال بالخدمة. لم تُعرض بيانات مخزنة على أنها حالية.",
      retryable: true,
      status,
    };
  }

  if (status === 401) {
    return {
      kind: "UNAUTHORIZED",
      code: detail.code ?? "SESSION_REQUIRED",
      message: "انتهت الجلسة أو لم تعد صالحة. أعد تسجيل الدخول للمتابعة.",
      reauthenticate: true,
      status,
    };
  }
  if (status === 403) {
    const code = detail.code ?? "FORBIDDEN";
    const isVerification = /verification|verify/i.test(`${code} ${detail.message ?? ""}`);
    return {
      kind: "FORBIDDEN",
      code,
      message: isVerification ? "يجب إكمال التحقق قبل استخدام الحساب." : "ليس لديك صلاحية لتنفيذ هذه العملية.",
      status,
    };
  }
  if (status === 409) {
    return {
      kind: "CONFLICT",
      code: detail.code ?? "CONTEXT_CONFLICT",
      message: "حدث تعارض في السياق. أعد تحميل السياق وحاول مرة أخرى.",
      retryable: true,
      status,
    };
  }
  if (status === 429) {
    const retryAfterHeader = hasResponse(error) ? error.response?.headers?.["retry-after"] : undefined;
    const retryAfterSeconds = Number.isFinite(Number(retryAfterHeader)) ? Number(retryAfterHeader) : undefined;
    return {
      kind: "RATE_LIMITED",
      code: "RATE_LIMITED",
      message: "تم تجاوز عدد المحاولات المسموح. انتظر قليلاً ثم حاول مجدداً.",
      retryable: true,
      retryAfterSeconds,
      status,
    };
  }
  if (status && status >= 500) {
    return {
      kind: "SERVER_UNAVAILABLE",
      code: "SERVICE_UNAVAILABLE",
      message: "الخدمة غير متاحة مؤقتاً. يمكنك إعادة المحاولة بأمان.",
      retryable: true,
      status,
    };
  }
  if (status === 400 || status === 422) {
    return {
      kind: "VALIDATION",
      code: detail.code ?? "VALIDATION_ERROR",
      message: detail.message_ar ?? detail.message ?? fallback,
      status,
    };
  }
  return {
    kind: "UNKNOWN",
    code: detail.code ?? "REQUEST_FAILED",
    message: detail.message_ar ?? detail.message ?? fallback,
    retryable: true,
    status,
  };
}

export function authFailureMessage(error: unknown): ApiErrorInfo {
  const info = classifyApiError(error, "تعذر تسجيل الدخول. تحقق من البيانات وحاول مرة أخرى.");
  if (info.status === 401) {
    return { ...info, code: "INVALID_CREDENTIALS", message: "تعذر تسجيل الدخول بالبيانات المقدمة." };
  }
  if (info.status === 403 && /verification|verify/i.test(info.code)) {
    return { ...info, code: "VERIFICATION_REQUIRED", message: "الحساب يحتاج إلى إكمال التحقق قبل تسجيل الدخول." };
  }
  if (info.status === 403 && /mfa/i.test(info.code)) {
    return { ...info, code: "MFA_REQUIRED", message: "يلزم إكمال إعداد المصادقة متعددة العوامل لهذا الحساب." };
  }
  if (info.status === 423) {
    return { ...info, code: "LOCKED", message: "تعذر تسجيل الدخول حالياً. حاول لاحقاً أو استخدم مسار الاسترداد." };
  }
  return info;
}
