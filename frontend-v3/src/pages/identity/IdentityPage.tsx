import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, Input, Button } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { identityApi } from "@/api/endpoints";
import { Link2, Search, CheckCircle, AlertCircle } from "lucide-react";

export function IdentityPage() {
  const [nationalId, setNationalId] = useState("");
  const [searchId, setSearchId] = useState("");
  const [linkPatientId, setLinkPatientId] = useState("");

  const { data: lookupResult, isLoading, error, refetch } = useQuery({
    queryKey: ["identity", "lookup", searchId],
    queryFn: () => identityApi.lookupByNid(searchId),
    enabled: !!searchId,
  });

  const linkMutation = useMutation({
    mutationFn: (data: { patient_id: number; national_id: string }) =>
      identityApi.linkNid(data),
  });

  const handleSearch = () => {
    if (nationalId.trim()) setSearchId(nationalId.trim());
  };

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
            <div className="flex gap-2">
              <Input
                placeholder="أدخل الرقم الوطني..."
                value={nationalId}
                onChange={(e) => setNationalId(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleSearch(); }}
              />
              <Button disabled={!nationalId} onClick={handleSearch}>
                <Search className="h-4 w-4" /> بحث
              </Button>
            </div>
            {isLoading && <LoadingSpinner />}
            {error && <ErrorDisplay error={(error as Error).message} onRetry={() => refetch()} />}
            {lookupResult && (
              <div className="p-4 bg-muted rounded-lg space-y-2">
                <div className="flex items-center gap-2 text-green-600">
                  <CheckCircle className="h-4 w-4" />
                  <span className="font-medium">تم العثور على السجل</span>
                </div>
                <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(lookupResult, null, 2)}</pre>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Link2 className="h-5 w-5" />
              ربط الهوية
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">رقم المريض</label>
              <Input
                placeholder="أدخل رقم المريض..."
                value={linkPatientId}
                onChange={(e) => setLinkPatientId(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">الرقم الوطني</label>
              <Input
                placeholder="أدخل الرقم الوطني..."
                value={nationalId}
                onChange={(e) => setNationalId(e.target.value)}
              />
            </div>
            <Button
              disabled={!linkPatientId || !nationalId || linkMutation.isPending}
              onClick={() =>
                linkMutation.mutate({
                  patient_id: Number(linkPatientId),
                  national_id: nationalId,
                })
              }
            >
              {linkMutation.isPending ? "جاري الربط..." : <Link2 className="h-4 w-4 ms-2" />}
              ربط
            </Button>
            {linkMutation.isSuccess && (
              <div className="flex items-center gap-2 text-green-600 text-sm">
                <CheckCircle className="h-4 w-4" />
                تم الربط بنجاح
              </div>
            )}
            {linkMutation.error && (
              <div className="flex items-center gap-2 text-destructive text-sm">
                <AlertCircle className="h-4 w-4" />
                {(linkMutation.error as Error).message}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
