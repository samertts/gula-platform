import { useCallback, useEffect, useMemo, useState } from "react";

type Platform = "android" | "windows" | "macos" | "linux" | "web";

type UpdatePolicy = {
  platform: Platform;
  current_version: string;
  latest_version: string;
  minimum_supported_version: string;
  update_available: boolean;
  force_update: boolean;
  store_url: string;
  release_notes_url: string;
  message: string;
  message_ar: string;
};

type UpdateManifest = {
  schema_version: number;
  generated_at: string;
  policies: Partial<Record<Platform, UpdatePolicy>>;
};

const APP_VERSION = import.meta.env.VITE_APP_VERSION || "2.5.0";
const MANIFEST_URL =
  import.meta.env.VITE_UPDATE_MANIFEST_URL ||
  "https://api.gula-platform.org/app-updates";
const CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000;

function compareVersions(left: string, right: string): number {
  const parse = (value: string) =>
    value
      .split(/[+-]/, 1)[0]
      ?.split(".")
      .slice(0, 3)
      .map((part) => Number.parseInt(part, 10) || 0) ?? [0, 0, 0];
  const a = parse(left);
  const b = parse(right);
  for (let index = 0; index < 3; index += 1) {
    const leftPart = a[index] ?? 0;
    const rightPart = b[index] ?? 0;
    if (leftPart !== rightPart) return leftPart - rightPart;
  }
  return 0;
}

function isValidPolicy(value: unknown): value is UpdatePolicy {
  if (!value || typeof value !== "object") return false;
  const policy = value as Partial<UpdatePolicy>;
  return (
    policy.platform === "web" &&
    typeof policy.latest_version === "string" &&
    typeof policy.minimum_supported_version === "string" &&
    typeof policy.store_url === "string" &&
    typeof policy.force_update === "boolean"
  );
}

export function UpdateGate({ children }: { children: React.ReactNode }) {
  const [policy, setPolicy] = useState<UpdatePolicy | null>(null);
  const [dismissed, setDismissed] = useState(false);

  const checkForUpdate = useCallback(async () => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 5000);
    try {
      const url = new URL(MANIFEST_URL);
      url.searchParams.set("platform", "web");
      url.searchParams.set("version", APP_VERSION);
      const response = await fetch(url, {
        headers: { Accept: "application/json" },
        cache: "no-store",
        signal: controller.signal,
      });
      if (!response.ok) return;
      const manifest = (await response.json()) as UpdateManifest;
      const candidate = manifest.policies?.web;
      if (isValidPolicy(candidate)) setPolicy(candidate);
    } catch {
      // A temporary manifest outage must not make the clinical UI unavailable.
    } finally {
      window.clearTimeout(timeout);
    }
  }, []);

  useEffect(() => {
    void checkForUpdate();
    const timer = window.setInterval(() => void checkForUpdate(), CHECK_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [checkForUpdate]);

  const isMandatory = useMemo(
    () => Boolean(policy?.force_update || compareVersions(APP_VERSION, policy?.minimum_supported_version || APP_VERSION) < 0),
    [policy],
  );
  const isOptional = Boolean(policy?.update_available && !isMandatory);

  const openUpdate = () => {
    if (policy?.platform === "web") {
      window.location.reload();
      return;
    }
    window.location.assign(policy?.store_url || "https://www.gula-platform.org/");
  };

  const showDialog = isMandatory || (isOptional && !dismissed);

  return (
    <>
      {!isMandatory && children}
      {showDialog && policy ? (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/70 p-4" role="dialog" aria-modal="true" aria-labelledby="update-title">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-teal-700">GULA Platform</p>
            <h2 id="update-title" className="text-xl font-bold text-slate-900">
              {isMandatory ? "تحديث مطلوب للمتابعة" : "يتوفر تحديث جديد"}
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              {policy.message_ar || "يتوفر إصدار أحدث من منصة GULA."}
            </p>
            <p className="mt-2 text-xs text-slate-500">
              الإصدار الحالي {APP_VERSION} · الإصدار الأحدث {policy.latest_version}
            </p>
            <div className="mt-6 flex justify-end gap-3">
              {!isMandatory ? (
                <button
                  type="button"
                  className="rounded-lg px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100"
                  onClick={() => setDismissed(true)}
                >
                  لاحقًا
                </button>
              ) : null}
              <button
                type="button"
                className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800"
                onClick={openUpdate}
              >
                {policy.platform === "web" ? "إعادة تحميل" : "تحديث الآن"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
