import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Input, Button, Dialog } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay } from "@/components/shared/PageComponents";
import { Search, Plus, Shield, CheckCircle2, XCircle } from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { Lab } from "@/types";

export function AdminLabsPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin-labs", search],
    queryFn: () => adminApi.labs({ limit: 50 }),
  });

  const columns: ColumnDef<Lab>[] = [
    { accessorKey: "name", header: "اسم المختبر" },
    { accessorKey: "city", header: "المدينة" },
    { accessorKey: "phone", header: "الهاتف" },
    { accessorKey: "license_number", header: "رقم الترخيص" },
    { accessorKey: "director_name", header: "المدير" },
    {
      accessorKey: "is_active",
      header: "الحالة",
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? "success" : "secondary"}>
          {row.original.is_active ? "نشط" : "غير نشط"}
        </Badge>
      ),
    },
  ];

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="إدارة المختبرات"
        description="إدارة ومراقبة المختبرات المسجلة على المنصة"
        actions={
          <Button>
            <Plus className="h-4 w-4" />
            إضافة مختبر
          </Button>
        }
      />
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={(data as any)?.items || (data as any)?.labs || []}
            loading={isLoading}
            toolbar={
              <div className="relative">
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input placeholder="بحث عن مختبر..." value={search} onChange={(e) => setSearch(e.target.value)} className="ps-9 w-80" />
              </div>
            }
          />
        </CardContent>
      </Card>
    </div>
  );
}

export function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin-users", search],
    queryFn: () => adminApi.users({ limit: 50 }),
  });

  const columns: ColumnDef<any>[] = [
    { accessorKey: "name", header: "الاسم" },
    { accessorKey: "email", header: "البريد الإلكتروني" },
    { accessorKey: "role", header: "الدور" },
    { accessorKey: "lab_name", header: "المختبر" },
    {
      accessorKey: "is_active",
      header: "الحالة",
      cell: ({ row }) => (
        <Badge variant={row.original.is_active ? "success" : "secondary"}>
          {row.original.is_active ? "نشط" : "غير نشط"}
        </Badge>
      ),
    },
  ];

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="إدارة المستخدمين"
        description="إدارة المستخدمين والصلاحيات"
        actions={
          <Button>
            <Plus className="h-4 w-4" />
            إضافة مستخدم
          </Button>
        }
      />
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={(data as any)?.items || (data as any)?.users || []}
            loading={isLoading}
            toolbar={
              <div className="relative">
                <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input placeholder="بحث عن مستخدم..." value={search} onChange={(e) => setSearch(e.target.value)} className="ps-9 w-80" />
              </div>
            }
          />
        </CardContent>
      </Card>
    </div>
  );
}

export function AdminAuditPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin-audit"],
    queryFn: () => adminApi.auditLogs({ limit: 50 }),
  });

  const columns: ColumnDef<any>[] = [
    { accessorKey: "action", header: "الإجراء" },
    { accessorKey: "entity_type", header: "الكيان" },
    { accessorKey: "entity_id", header: "رقم الكيان" },
    { accessorKey: "user_name", header: "المستخدم" },
    { accessorKey: "created_at", header: "التاريخ" },
  ];

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <PageHeader title="سجل التدقيق" description="سجل جميع العمليات على المنصة" />
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={(data as any)?.items || (data as any)?.logs || []}
            loading={isLoading}
          />
        </CardContent>
      </Card>
    </div>
  );
}
