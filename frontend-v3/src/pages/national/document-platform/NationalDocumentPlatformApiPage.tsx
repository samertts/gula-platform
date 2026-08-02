import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { PageHeader } from "@/components/shared/PageComponents";
import { DataTable, Card, CardContent, Badge } from "@/components/ui";



import { asTableData } from "@/lib/utils";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import {  FolderOpen, Activity, BookOpen, ClipboardList, FileText, List } from "lucide-react";

const tabs = [
  { id: "documents", label: "المستندات", icon: FileText },
  { id: "versions", label: "versions", icon: Activity },
  { id: "signatures", label: "signatures", icon: List },
  { id: "qrcode", label: "qrcode", icon: ClipboardList },
  { id: "attachments", label: "attachments", icon: BookOpen },
  { id: "history", label: "history", icon:  FolderOpen },
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

export default function NationalDocumentPlatformApiPage() {
  const [activeTab, setActiveTab] = useState<TabId>("documents");
  const col = createColumnHelper<Record<string, unknown>>();

  const documents = useQuery({
    queryKey: ["nationalDocumentPlatformApi", "documents"],
    queryFn: () => api.get("/national/documents").then((r) => r.data),
  });
  const versions = useQuery({
    queryKey: ["nationalDocumentPlatformApi", "versions"],
    enabled: false,
    queryFn: () => api.get("/national/documents//versions").then((r) => r.data),
  });
  const signatures = useQuery({
    queryKey: ["nationalDocumentPlatformApi", "signatures"],
    enabled: false,
    queryFn: () => api.get("/national/documents//signatures").then((r) => r.data),
  });
  const qrcode = useQuery({
    queryKey: ["nationalDocumentPlatformApi", "qrcode"],
    enabled: false,
    queryFn: () => api.get("/national/documents//qrcode").then((r) => r.data),
  });
  const attachments = useQuery({
    queryKey: ["nationalDocumentPlatformApi", "attachments"],
    enabled: false,
    queryFn: () => api.get("/national/documents//attachments").then((r) => r.data),
  });
  const history = useQuery({
    queryKey: ["nationalDocumentPlatformApi", "history"],
    enabled: false,
    queryFn: () => api.get("/national/documents//history").then((r) => r.data),
  });

  const documentsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const versionsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const signaturesCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const qrcodeCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const attachmentsCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];
  const historyCols: ColumnDef<Record<string, unknown>, unknown>[] = [
    col.accessor("id", { header: "المعرف" }),
    col.accessor("name", { header: "الاسم" }),
    col.accessor("status", { header: "الحالة", cell: ({ getValue }) => <Badge variant={badgeVariant(getValue() as string)}>{getValue() as string}</Badge> }),
    col.accessor("created_at", { header: "التاريخ", cell: ({ getValue }) => new Date(getValue() as string).toLocaleDateString("ar-IQ") }),
  ];

  const tables: Record<TabId, { columns: ColumnDef<Record<string, unknown>, unknown>[]; data: Record<string, unknown>[]; loading: boolean; error: Error | null; onRetry: () => void }> = {
    documents: { columns: documentsCols, data: asTableData(documents.data), loading: documents.isLoading, error: documents.error, onRetry: () => documents.refetch() },
    versions: { columns: versionsCols, data: asTableData(versions.data), loading: versions.isLoading, error: versions.error, onRetry: () => versions.refetch() },
    signatures: { columns: signaturesCols, data: asTableData(signatures.data), loading: signatures.isLoading, error: signatures.error, onRetry: () => signatures.refetch() },
    qrcode: { columns: qrcodeCols, data: asTableData(qrcode.data), loading: qrcode.isLoading, error: qrcode.error, onRetry: () => qrcode.refetch() },
    attachments: { columns: attachmentsCols, data: asTableData(attachments.data), loading: attachments.isLoading, error: attachments.error, onRetry: () => attachments.refetch() },
    history: { columns: historyCols, data: asTableData(history.data), loading: history.isLoading, error: history.error, onRetry: () => history.refetch() },
  };

  return (
    <div className="space-y-6">
      <PageHeader title="الوثائق الوطنية" description="إدارة الوثائق الوطنية" />
      <Card>
        <CardContent className="p-0">
          <div className="flex border-b flex-wrap">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button key={tab.id} role="tab" aria-selected={activeTab === tab.id} onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.id ? "border-b-2 border-indigo-600 text-indigo-600" : "text-gray-500 hover:text-gray-700"}`}>
                  <Icon className="h-4 w-4" />{tab.label}
                </button>
              );
            })}
          </div>
          <div className="p-4">
            <DataTable columns={tables[activeTab].columns} data={tables[activeTab].data} loading={tables[activeTab].loading} error={tables[activeTab].error} onRetry={tables[activeTab].onRetry} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
