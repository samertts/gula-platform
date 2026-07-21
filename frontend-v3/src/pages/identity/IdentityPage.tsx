import { Card, CardContent, CardHeader, CardTitle, Input, Button } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { Fingerprint, Link2, Search } from "lucide-react";
import { useState } from "react";

export function IdentityPage() {
  const [nationalId, setNationalId] = useState("");

  return (
    <div className="space-y-6">
      <PageHeader title="الهوية الصحية" description="ربط الهوية الوطنية بالسجلات الصحية" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              البحث بالهوية الوطنية
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">الرقم الوطني</label>
              <Input
                placeholder="أدخل الرقم الوطني..."
                value={nationalId}
                onChange={(e) => setNationalId(e.target.value)}
              />
            </div>
            <Button disabled={!nationalId}>
              <Fingerprint className="h-4 w-4" /> بحث
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Link2 className="h-5 w-5" />
              ربط الهوية
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              ربط الرقم الوطني للمريض بسجله الصحي في المنصة
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
