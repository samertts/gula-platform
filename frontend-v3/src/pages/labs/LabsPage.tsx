import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Input, Button } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { Search, Plus } from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { Lab } from "@/types";

export function LabsPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["labs", search],
    queryFn: () => adminApi.labs({ limit: 50 }),
  });

  const columns: ColumnDef<Lab>[] = [
    { accessorKey: "name", header: "اسم المختبر" },
    { accessorKey: "city", header: "المدينة" },
    { accessorKey: "phone", header: "الهاتف" },
    { accessorKey: "license_number", header: "رقم الترخيص" },
    { accessorKey: "director_name", header: "اسم المدير" },
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

  return (
    <div className="space-y-6">
      <PageHeader
        title="المختبرات"
        description="إدارة المختبرات المسجلة على المنصة"
        actions={
          <Button>
            <Plus className="h-4 w-4" />
            مختبر جديد
          </Button>
        }
      />
      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={(data as any)?.labs || (data as any)?.items || []}
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
