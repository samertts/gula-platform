import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return "—";
  const d = new Date(date);
  return d.toLocaleDateString("ar-IQ", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return "—";
  const d = new Date(date);
  return d.toLocaleDateString("ar-IQ", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatNumber(n: number | null | undefined): string {
  if (n == null) return "—";
  return new Intl.NumberFormat("ar-IQ").format(n);
}

export function getFlagColor(flag: string | null | undefined): string {
  switch (flag) {
    case "critical":
      return "text-red-600 bg-red-50 dark:bg-red-950";
    case "H":
    case "high":
      return "text-orange-600 bg-orange-50 dark:bg-orange-950";
    case "L":
    case "low":
      return "text-yellow-600 bg-yellow-50 dark:bg-yellow-950";
    case "normal":
      return "text-green-600 bg-green-50 dark:bg-green-950";
    default:
      return "text-gray-600 bg-gray-50 dark:bg-gray-900";
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case "active":
    case "completed":
    case "validated":
    case "verified":
    case "approved":
      return "text-green-600 bg-green-50 dark:bg-green-950 border-green-200";
    case "pending":
    case "pending_verification":
    case "pending_approval":
      return "text-yellow-600 bg-yellow-50 dark:bg-yellow-950 border-yellow-200";
    case "cancelled":
    case "rejected":
    case "failed":
      return "text-red-600 bg-red-50 dark:bg-red-950 border-red-200";
    case "inactive":
    case "suspended":
      return "text-gray-600 bg-gray-50 dark:bg-gray-900 border-gray-200";
    default:
      return "text-blue-600 bg-blue-50 dark:bg-blue-950 border-blue-200";
  }
}

export function getGenderLabel(gender: string | null | undefined): string {
  if (!gender) return "—";
  const map: Record<string, string> = {
    M: "ذكر",
    male: "ذكر",
    F: "أنثى",
    female: "أنثى",
  };
  return map[gender] ?? gender;
}

export function getLabTypeLabel(type: string): string {
  const map: Record<string, string> = {
    private: "خاص",
    government: "حكومي",
    hospital: "مستشفى",
    clinic: "عيادة",
  };
  return map[type] ?? type;
}

export function getRoleLabel(role: string): string {
  const map: Record<string, string> = {
    master_admin: "مدير النظام",
    ministry_admin: "مدير وزارة",
    province_admin: "مدير محافظة",
    admin: "مدير مختبر",
    lab_admin: "مدير مختبر",
    doctor: "طبيب",
    technician: "فني مختبر",
    staff: "موظف",
    receptionist: "موظف استقبال",
    citizen: "مواطن",
    pathologist: "أخصائي علم أمراض",
    nurse: "ممرض",
  };
  return map[role] ?? role;
}

export function getTierLabel(tier: string): string {
  const map: Record<string, string> = {
    starter: "البداية",
    growth: "النمو",
    enterprise: "المؤسسات",
  };
  return map[tier] ?? tier;
}

export function getTierColor(tier: string): string {
  const map: Record<string, string> = {
    starter: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
    growth: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
    enterprise: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
  };
  return map[tier] ?? "bg-gray-100 text-gray-700";
}

const COLLECTION_KEYS = ["items", "data", "results", "records", "logs", "metrics", "traces", "jobs", "schedules", "tasks", "documents", "rules", "notifications", "suspensions", "certificates", "identities", "providers", "agreements", "frameworks", "profiles", "anchors", "definitions", "instances", "policies"] as const;

export function asTableData<T = Record<string, unknown>>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (value && typeof value === "object") {
    for (const key of COLLECTION_KEYS) {
      const candidate = (value as Record<string, unknown>)[key];
      if (Array.isArray(candidate)) return candidate as T[];
    }
  }
  return [];
}

interface ApiErrorLike {
  response?: { data?: { detail?: string | { msg?: string }[] } };
  message?: string;
}

export function getErrorMessage(err: unknown, fallback = "حدث خطأ غير متوقع"): string {
  if (!err) return fallback;
  const e = err as ApiErrorLike;
  const detail = e.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  if (typeof e.message === "string" && e.message !== "Request failed with status code 401") {
    return e.message;
  }
  return fallback;
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function openInNewTab(url: string): void {
  window.open(url, "_blank", "noopener,noreferrer");
}
