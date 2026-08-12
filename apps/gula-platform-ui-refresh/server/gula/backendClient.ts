export const GULA_AUTHORIZATION_CONTEXT_CONTRACT = {
  id: "authorization.context.read",
  method: "GET",
  path: "/authz/me",
  permission: "جلسة مستخدم صالحة",
  requiresWorkspaceContext: false,
} as const;

type Environment = Record<string, string | undefined>;

type FetchResponse = {
  ok: boolean;
  status: number;
};

type Fetcher = (input: string, init: RequestInit) => Promise<FetchResponse>;

export type GulaConnectionStatus = {
  state: "not_configured" | "configuration_invalid" | "ready";
  label: string;
  description: string;
  contractId: typeof GULA_AUTHORIZATION_CONTEXT_CONTRACT.id;
  requiredPermission: typeof GULA_AUTHORIZATION_CONTEXT_CONTRACT.permission;
  requiresWorkspaceContext: typeof GULA_AUTHORIZATION_CONTEXT_CONTRACT.requiresWorkspaceContext;
  verificationAvailable: boolean;
};

export type GulaVerificationResult = {
  state: "not_configured" | "configuration_invalid" | "unavailable" | "verified";
  label: string;
  description: string;
  contractId: typeof GULA_AUTHORIZATION_CONTEXT_CONTRACT.id;
  statusCode?: number;
};

function getConfiguredUrl(env: Environment): string | null {
  const rawUrl = env.GULA_BACKEND_BASE_URL?.trim();
  if (!rawUrl) return null;

  try {
    const parsed = new URL(rawUrl);
    if (parsed.protocol !== "https:" && parsed.protocol !== "http:") return null;
    return parsed.toString().replace(/\/$/, "");
  } catch {
    return null;
  }
}

function hasBackendToken(env: Environment): boolean {
  return Boolean(env.GULA_BACKEND_SERVICE_TOKEN?.trim());
}

export function getGulaConnectionStatus(env: Environment = process.env): GulaConnectionStatus {
  const baseUrlProvided = Boolean(env.GULA_BACKEND_BASE_URL?.trim());
  const tokenProvided = hasBackendToken(env);
  const baseUrl = getConfiguredUrl(env);

  if (!baseUrlProvided || !tokenProvided) {
    return {
      state: "not_configured",
      label: "الاتصال الخادمي غير مُعدّ",
      description: "لم يُضبط عنوان الخلفية أو رمز الخدمة الخادمي. لا تُجرى أي طلبات خارجية ولا تُعرض بيانات تشغيلية.",
      contractId: GULA_AUTHORIZATION_CONTEXT_CONTRACT.id,
      requiredPermission: GULA_AUTHORIZATION_CONTEXT_CONTRACT.permission,
      requiresWorkspaceContext: GULA_AUTHORIZATION_CONTEXT_CONTRACT.requiresWorkspaceContext,
      verificationAvailable: false,
    };
  }

  if (!baseUrl) {
    return {
      state: "configuration_invalid",
      label: "إعداد عنوان الخلفية غير صالح",
      description: "عنوان خدمة الخلفية يجب أن يكون رابط HTTP أو HTTPS صالحًا. لم تُجرَ أي محاولة اتصال.",
      contractId: GULA_AUTHORIZATION_CONTEXT_CONTRACT.id,
      requiredPermission: GULA_AUTHORIZATION_CONTEXT_CONTRACT.permission,
      requiresWorkspaceContext: GULA_AUTHORIZATION_CONTEXT_CONTRACT.requiresWorkspaceContext,
      verificationAvailable: false,
    };
  }

  return {
    state: "ready",
    label: "الاتصال الخادمي جاهز للتحقق",
    description: "يتوفر إعداد خادمي لعقد سياق التفويض. يلزم تحقق إداري صريح قبل اعتبار أي خدمة تشغيلية متاحة.",
    contractId: GULA_AUTHORIZATION_CONTEXT_CONTRACT.id,
    requiredPermission: GULA_AUTHORIZATION_CONTEXT_CONTRACT.permission,
    requiresWorkspaceContext: GULA_AUTHORIZATION_CONTEXT_CONTRACT.requiresWorkspaceContext,
    verificationAvailable: true,
  };
}

export async function verifyGulaAuthorizationContext(
  env: Environment = process.env,
  fetcher: Fetcher = (input, init) => fetch(input, init),
): Promise<GulaVerificationResult> {
  const status = getGulaConnectionStatus(env);
  if (status.state === "not_configured") {
    return {
      state: "not_configured",
      label: status.label,
      description: status.description,
      contractId: status.contractId,
    };
  }

  if (status.state === "configuration_invalid") {
    return {
      state: "configuration_invalid",
      label: status.label,
      description: status.description,
      contractId: status.contractId,
    };
  }

  const baseUrl = getConfiguredUrl(env);
  const token = env.GULA_BACKEND_SERVICE_TOKEN?.trim();
  if (!baseUrl || !token) {
    return {
      state: "not_configured",
      label: "الاتصال الخادمي غير مُعدّ",
      description: "لم تُجرَ أي محاولة اتصال لغياب إعداد خادمي كامل.",
      contractId: GULA_AUTHORIZATION_CONTEXT_CONTRACT.id,
    };
  }

  try {
    const response = await fetcher(`${baseUrl}${GULA_AUTHORIZATION_CONTEXT_CONTRACT.path}`, {
      method: GULA_AUTHORIZATION_CONTEXT_CONTRACT.method,
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      return {
        state: "unavailable",
        label: "تعذر التحقق من عقد الخلفية",
        description: "رفضت خدمة الخلفية طلب التحقق أو لم تكن متاحة. لم تُعرض أي بيانات من الاستجابة.",
        contractId: GULA_AUTHORIZATION_CONTEXT_CONTRACT.id,
        statusCode: response.status,
      };
    }

    return {
      state: "verified",
      label: "تم التحقق الخادمي من العقد",
      description: "نجح فحص عقد سياق التفويض عبر الخادم. لا يعني ذلك تفويضًا تشغيليًا لمستخدم الواجهة؛ يظل الخادم مصدر القرار النهائي.",
      contractId: GULA_AUTHORIZATION_CONTEXT_CONTRACT.id,
      statusCode: response.status,
    };
  } catch {
    return {
      state: "unavailable",
      label: "تعذر الاتصال بخدمة الخلفية",
      description: "لم يكتمل طلب التحقق الخادمي. لم تُعرض أي بيانات تشغيلية.",
      contractId: GULA_AUTHORIZATION_CONTEXT_CONTRACT.id,
    };
  }
}
