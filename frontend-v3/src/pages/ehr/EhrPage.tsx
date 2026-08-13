import { LegacyRouteBridge } from "@/pages/migration/LegacyRouteBridge";

/**
 * لا تملك frontend-v3 قناة جلسة وسياق منشأة متوافقة مع عقد
 * clinical.ehr.record.read. لذلك لا يجوز لهذه الصفحة استدعاء المرضى أو
 * الطلبات أو النتائج عبر REST مباشرةً، حتى لو كانت المسارات القديمة موجودة.
 */
export function EhrPage() {
  return <LegacyRouteBridge />;
}
