import { Link, Navigate, useLocation } from "react-router-dom";
import { specialtyEntrypoints, type LegacyRouteRule } from "./frontendSurfaceCatalog";

/**
 * مسارات frontend-v2 التي ثبتت لها مكافئات وظيفية في frontend-v3.
 * لا تتحول المسارات من دون مكافئ مثبت إلى صفحة تشغيلية كي لا تتجاوز
 * الصلاحيات أو تخلط بين عقود مختلفة.
 */
export const legacyRouteRules: Record<string, LegacyRouteRule> = {
  "/patients": {
    target: "/patients",
    title: "سجل المرضى",
    rationale: "يعتمد المسار الموحد على بوابة سياق المنشأة قبل القراءة.",
  },
  "/settings": {
    target: "/settings",
    title: "الإعدادات",
    rationale: "يتوفر مسار إعدادات مكافئ في الواجهة الموحدة.",
  },
  "/lab/dashboard": {
    target: "/dashboard",
    title: "لوحة المختبر",
    rationale: "تعرض لوحة v3 حالة اتصال حوكمية ولا تعرض مؤشرات غير موثقة.",
  },
  "/lab/queue": {
    target: "/orders",
    title: "قائمة عمل المختبر",
    rationale: "تم توحيد قائمة الطلبات خلف عقد القراءة النطاقي.",
  },
  "/lab/samples": {
    target: "/samples",
    title: "تتبع العينات",
    rationale: "يتوفر مسار عينات محمي في frontend-v3.",
  },
  "/lab/qc": {
    target: "/qc",
    title: "ضبط الجودة",
    rationale: "يتوفر مسار ضبط جودة محمي في frontend-v3.",
  },
  "/admin/audit": {
    target: "/admin/audit",
    title: "سجل التدقيق",
    rationale: "يحافظ المسار الموحد على حارس الأدوار الإداري.",
  },
  "/citizen/dashboard": {
    target: "/citizen",
    title: "مساحة المواطن",
    rationale: "تُحفظ حماية دور المواطن في المسار الموحد.",
  },
  "/citizen/consent": {
    target: "/capabilities/healthcare-consent",
    title: "الموافقة الصحية",
    rationale: "يستبدل العقد الموحد صفحة الموافقة القديمة دون نقل بيانات تمثيلية.",
  },
  "/citizen/verification": {
    target: "/identity",
    title: "التحقق من الهوية",
    rationale: "يستخدم المسار الموحد حماية أدوار الموظفين.",
  },
  "/ministry/dashboard": {
    target: "/national-data",
    title: "لوحة البيانات الوطنية",
    rationale: "يستبقي المسار الموحد الحارس الخاص بالأدوار الوزارية.",
  },
};

export function resolveLegacyRoute(pathname: string): LegacyRouteRule | undefined {
  const directRule = legacyRouteRules[pathname];
  if (directRule) return directRule;

  const firstSegment = `/${pathname.split("/").filter(Boolean)[0] ?? ""}`;
  const entrypoint = specialtyEntrypoints[firstSegment];
  if (!entrypoint) return undefined;

  if (pathname === firstSegment || pathname === `${firstSegment}/`) return entrypoint;

  return {
    title: entrypoint.title,
    rationale: `المسار الفرعي ${pathname} ضمن ${entrypoint.title} ما زال قيد التوحيد. ${entrypoint.rationale}`,
  };
}

export function LegacyRouteBridge() {
  const { pathname } = useLocation();
  const rule = resolveLegacyRoute(pathname);

  if (rule?.target && rule.target !== pathname) {
    return <Navigate to={rule.target} replace />;
  }

  return (
    <section className="mx-auto flex min-h-[58vh] max-w-2xl items-center justify-center px-5" dir="rtl" aria-labelledby="legacy-route-title">
      <div className="w-full rounded-3xl border border-slate-200 bg-white p-8 text-right shadow-sm">
        <p className="text-sm font-bold text-emerald-700">مسار انتقالي موحّد</p>
        <h1 id="legacy-route-title" className="mt-2 text-2xl font-extrabold text-slate-900">
          {rule?.title ?? "هذا المسار قيد التوحيد داخل frontend-v3"}
        </h1>
        <p className="mt-4 leading-7 text-slate-600">
          {rule?.rationale ?? "لا يوجد مكافئ موثق لهذا المسار القديم بعد. أُبقي الوصول في الواجهة الموحدة صريحًا بدل إعادة توجيهه إلى وظيفة مختلفة أو تفعيل عقد غير معتمد."}
        </p>
        <p className="mt-3 rounded-xl bg-slate-50 px-4 py-3 font-mono text-xs text-slate-500" dir="ltr">
          {pathname}
        </p>
        <Link
          to="/dashboard"
          className="mt-6 inline-flex items-center rounded-xl bg-slate-900 px-5 py-3 text-sm font-bold text-white transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2"
        >
          العودة إلى لوحة التحكم الموحدة
        </Link>
      </div>
    </section>
  );
}
