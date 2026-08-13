import { Bell, Building2, LockKeyhole, Palette, UsersRound } from "lucide-react";

const settingItems = [
  { icon: Building2, title: "بيانات المختبر", description: "الاسم والعنوان ووسائل الاتصال" },
  { icon: UsersRound, title: "إدارة المستخدمين", description: "الأدوار والصلاحيات وفرق العمل" },
  { icon: Bell, title: "التنبيهات والإشعارات", description: "قواعد التنبيه وقنوات الإرسال" },
  { icon: LockKeyhole, title: "الخصوصية والأمان", description: "سياسات الوصول وسجل النشاط" },
  { icon: Palette, title: "تفضيلات الواجهة", description: "خيارات العرض واللغة" },
];

export default function Settings() {
  return <div className="page-stack page-enter"><section className="page-hero"><div><span className="section-kicker">إعدادات المنصة</span><h2>الإعدادات</h2><p>تظهر مجالات الإعداد هنا، لكن التعديل يبقى غير متاح إلى أن تتصل كل مساحة بعقدها وصلاحيتها المعتمدة.</p></div></section><section className="settings-list panel" aria-label="مجالات الإعداد غير المربوطة">{settingItems.map((item) => { const Icon = item.icon; return <article className="settings-row settings-row--unavailable" key={item.title}><span className="settings-icon"><Icon size={20} /></span><span><b>{item.title}</b><small>{item.description}</small></span><em>يتطلب ربطًا معتمدًا</em></article>})}</section></div>;
}
