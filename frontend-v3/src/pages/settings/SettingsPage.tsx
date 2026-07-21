import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { Settings2, Bell, Shield, Palette, Globe } from "lucide-react";

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="الإعدادات" description="إعدادات النظام والتفضيلات" />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {[
          { icon: Globe, title: "اللغة والمنطقة", desc: "تغيير لغة النظام وإعدادات المنطقة" },
          { icon: Palette, title: "المظهر", desc: "تخصيص ألوان وثيم النظام" },
          { icon: Bell, title: "الإشعارات", desc: "إعدادات التنبيهات والإشعارات" },
          { icon: Shield, title: "الأمان", desc: "إعدادات كلمة المرور والمصادقة" },
          { icon: Settings2, title: "عام", desc: "الإعدادات العامة للنظام" },
        ].map((item) => (
          <Card key={item.title} className="cursor-pointer hover:bg-accent transition-colors">
            <CardContent className="flex items-start gap-4 p-6">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <item.icon className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-base">{item.title}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">{item.desc}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
