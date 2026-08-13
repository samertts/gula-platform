import { LegacyRouteBridge } from "@/pages/migration/LegacyRouteBridge";

/**
 * لا تعرض النتائج عبر REST مباشر: عقد test-results.read لا يكفي دون إثبات
 * فرض سياق المنشأة والصلاحية على الخادم أو اعتماد قناة tRPC/بوابة موحدة.
 */
export function ResultsPage() {
  return <LegacyRouteBridge />;
}
