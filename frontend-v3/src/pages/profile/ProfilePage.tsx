import { Card, CardContent, CardHeader, CardTitle, Input, Button, Badge } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { useAuth } from "@/contexts/AuthContext";
import { User, Mail, Shield, Building2 } from "lucide-react";

export function ProfilePage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <PageHeader title="الملف الشخصي" description="معلومات حسابك الشخصي" />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardContent className="flex flex-col items-center p-6 text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10 text-3xl font-bold text-primary">
              {user?.name?.charAt(0) || "U"}
            </div>
            <h2 className="mt-4 text-xl font-bold">{user?.name}</h2>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
            <Badge className="mt-2">{user?.role}</Badge>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>معلومات الحساب</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2"><User className="h-4 w-4" /> الاسم</label>
              <Input value={user?.name || ""} readOnly />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2"><Mail className="h-4 w-4" /> البريد الإلكتروني</label>
              <Input value={user?.email || ""} readOnly />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2"><Shield className="h-4 w-4" /> الدور</label>
              <Input value={user?.role || ""} readOnly />
            </div>
            {user?.lab_name && (
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2"><Building2 className="h-4 w-4" /> المختبر</label>
                <Input value={user.lab_name} readOnly />
              </div>
            )}
            <div className="pt-4">
              <Button variant="outline">تعديل المعلومات</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
