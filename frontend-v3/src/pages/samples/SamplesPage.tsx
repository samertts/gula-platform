import { LegacyRouteBridge } from "@/pages/migration/LegacyRouteBridge";

/**
 * لا يوجد عقد قراءة عينات مؤهل في السجل الحالي؛ لذلك لا يُعاد استخدام REST
 * المباشر لعرض بيانات مخبرية إلى أن يثبت العقد والسياق والتفويض الخادمي.
 */
export function SamplesPage() {
  return <LegacyRouteBridge />;
}
