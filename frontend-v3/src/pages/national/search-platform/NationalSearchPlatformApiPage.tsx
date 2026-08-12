import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable } from "@/components/ui/DataTable";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {  FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "search", label: "search", icon: FileText },
  { id: "suggest", label: "suggest", icon: Activity },
  { id: "facets", label: "facets", icon: List },
  { id: "saved", label: "saved", icon: ClipboardList },
  { id: "stats", label: "stats", icon: BookOpen },
  { id: "health", label: "الحالة", icon:  FolderOpen },
] as const;

type TabId = (typeof tabs)[number]["id"];

const badgeVariant = (s: string) => {
  const m: Record<string, "success" | "warning" | "destructive" | "default"> = {
    active: "success", completed: "success", approved: "success",
    pending: "warning", draft: "default", rejected: "destructive",
    inactive: "default", expired: "warning", revoked: "destructive",
  };
  return m[s?.toLowerCase()] ?? "default";
};

export default function NationalSearchPlatformApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("search");
  const col = createColumnHelper<Record<string, unknown>>();

  const search = useQuery({
    queryKey: ["nationalSearchPlatformApi", "search"],
    queryFn: () => api.get("/national/search/search").then((r) => r.data),
  });
  const suggest = useQuery({
    queryKey: ["nationalSearchPlatformApi", "suggest"],
    queryFn: () => api.get("/national/search/suggest").then((r) => r.data),
  });
  const facets = useQuery({
    queryKey: ["nationalSearchPlatformApi", "facets"],
    queryFn: () => api.get("/national/search/facets").then((r) => r.data),
  });
  const saved = useQuery({
    queryKey: ["nationalSearchPlatformApi", "saved"],
    queryFn: () => api.get("/national/search/saved").then((r) => r.data),
  });
  const stats = useQuery({
    queryKey: ["nationalSearchPlatformApi", "stats"],
    queryFn: () => api.get("/national/search/stats").then((r) => r.data),
  });
  const health = useQuery({
    queryKey: ["nationalSearchPlatformApi", "health"],
    queryFn: () => api.get("/national/search/health").then((r) => r.data),
  });

  const searchCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const suggestCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const facetsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const savedCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const statsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const healthCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean }> = {
    search: { columns: searchCols, data: (search.data ?? []) as Record<string, unknown>[], loading: search.isLoading },
    suggest: { columns: suggestCols, data: (suggest.data ?? []) as Record<string, unknown>[], loading: suggest.isLoading },
    facets: { columns: facetsCols, data: (facets.data ?? []) as Record<string, unknown>[], loading: facets.isLoading },
    saved: { columns: savedCols, data: (saved.data ?? []) as Record<string, unknown>[], loading: saved.isLoading },
    stats: { columns: statsCols, data: (stats.data ?? []) as Record<string, unknown>[], loading: stats.isLoading },
    health: { columns: healthCols, data: (health.data ?? []) as Record<string, unknown>[], loading: health.isLoading },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="البحث الوطني" description="إدارة البحث الوطني" />
      <Card>
        <CardContent className="p-0">
          <div className="flex border-b flex-wrap">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.id ? "border-b-2 border-indigo-600 text-indigo-600" : "text-gray-500 hover:text-gray-700"}`}>
                  <Icon className="h-4 w-4" />{tab.label}
                </button>
              );
            })}
          </div>
          <div className="p-4">
            <DataTable columns={tables[activeTab].columns} data={tables[activeTab].data} loading={tables[activeTab].loading} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
