import { useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";
import { financialApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, DataTable } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay, EmptyState } from "@/components/shared/PageComponents";
import { DollarSign, FileText, CreditCard, ArrowLeftRight } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

const tabs = [
  { id: "overview", label: "نظرة عامة", icon: DollarSign },
  { id: "invoices", label: "الفواتير", icon: FileText },
  { id: "payments", label: "المدفوعات", icon: CreditCard },
  { id: "transactions", label: "المعاملات", icon: ArrowLeftRight },
] as const;

type TabId = (typeof tabs)[number]["id"];

function extractList(data: unknown): unknown[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    return (obj.items as unknown[]) || (obj.data as unknown[]) || (obj.results as unknown[]) || [];
  }
  return [];
}

function statusBadge(status: string | undefined | null) {
  if (!status) return <Badge variant="outline">-</Badge>;
  const s = status.toLowerCase();
  if (s === "paid" || s === "completed") return <Badge variant="success">{status}</Badge>;
  if (s === "pending" || s === "unpaid") return <Badge variant="warning">{status}</Badge>;
  if (s === "cancelled" || s === "failed") return <Badge variant="destructive">{status}</Badge>;
  return <Badge>{status}</Badge>;
}

function formatCurrency(amount: unknown) {
  if (amount == null) return "-";
  const n = typeof amount === "string" ? parseFloat(amount) : Number(amount);
  if (isNaN(n)) return String(amount);
  return new Intl.NumberFormat("ar-IQ", { style: "currency", currency: "IQD" }).format(n);
}

function formatDate(d: unknown) {
  if (!d) return "-";
  try {
    return new Intl.DateTimeFormat("ar-IQ", {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(new Date(String(d)));
  } catch {
    return String(d);
  }
}

function OverviewTab() {
  const statusQuery = useQuery({
    queryKey: ["financial", "billing-status"],
    queryFn: () => financialApi.billingStatus(),
  });
  const ratesQuery = useQuery({
    queryKey: ["financial", "billing-rates"],
    queryFn: () => financialApi.billingRates(),
  });

  if (statusQuery.isLoading || ratesQuery.isLoading) return <LoadingSpinner />;
  if (statusQuery.error) return <ErrorDisplay error={statusQuery.error?.message} onRetry={() => statusQuery.refetch()} />;
  if (ratesQuery.error) return <ErrorDisplay error={ratesQuery.error?.message} onRetry={() => ratesQuery.refetch()} />;

  const status = statusQuery.data as Record<string, unknown> | undefined;
  const rates = ratesQuery.data as Record<string, unknown> | undefined;

  const metrics = [
    {
      label: "إجمالي الفواتير",
      value: status?.total_invoices ?? status?.invoices_count ?? 0,
      icon: FileText,
      color: "text-blue-600",
      bg: "bg-blue-100 dark:bg-blue-900/30",
    },
    {
      label: "المدفوعات المستلمة",
      value: status?.total_paid ?? status?.paid_amount ?? 0,
      icon: DollarSign,
      color: "text-emerald-600",
      bg: "bg-emerald-100 dark:bg-emerald-900/30",
      currency: true,
    },
    {
      label: "المبالغ المستحقة",
      value: status?.total_due ?? status?.due_amount ?? 0,
      icon: CreditCard,
      color: "text-amber-600",
      bg: "bg-amber-100 dark:bg-amber-900/30",
      currency: true,
    },
    {
      label: "عدد المعاملات",
      value: status?.total_transactions ?? status?.transactions_count ?? 0,
      icon: ArrowLeftRight,
      color: "text-purple-600",
      bg: "bg-purple-100 dark:bg-purple-900/30",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => (
          <Card key={m.label}>
            <CardContent className="flex items-center gap-4 p-6">
              <div className={`flex h-12 w-12 items-center justify-center rounded-full ${m.bg}`}>
                <m.icon className={`h-6 w-6 ${m.color}`} />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">{m.label}</p>
                <p className="text-2xl font-bold">
                  {m.currency ? formatCurrency(m.value as number) : String(m.value ?? 0)}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {rates && Object.keys(rates).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>أسعار الفوترة</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(rates).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between rounded-lg border p-3">
                  <span className="text-sm text-muted-foreground">{key}</span>
                  <span className="font-semibold">{formatCurrency(value as number)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function InvoicesTab() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["financial", "invoices"],
    queryFn: () => financialApi.listInvoices(),
  });

  const invoices = extractList(data);

  const columns: ColumnDef<Record<string, unknown>>[] = [
    { accessorKey: "id", header: "رقم الفاتورة" },
    { accessorKey: "amount", header: "المبلغ", cell: ({ row }) => formatCurrency(row.original.amount) },
    { accessorKey: "status", header: "الحالة", cell: ({ row }) => statusBadge(row.original.status as string) },
    {
      id: "patient",
      header: "المريض / المختبر",
      cell: ({ row }) => row.original.patient_name || row.original.lab_name || "-",
    },
    { accessorKey: "created_at", header: "تاريخ الإنشاء", cell: ({ row }) => formatDate(row.original.created_at as string) },
    { accessorKey: "due_date", header: "تاريخ الاستحقاق", cell: ({ row }) => formatDate(row.original.due_date as string) },
  ];

  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <Card>
      <CardContent className="pt-6">
        {!isLoading && invoices.length === 0 ? (
          <EmptyState icon={FileText} title="لا توجد فواتير" description="لم يتم إنشاء أي فواتير بعد" />
        ) : (
          <DataTable columns={columns} data={invoices as Record<string, unknown>[]} loading={isLoading} />
        )}
      </CardContent>
    </Card>
  );
}

function PaymentsTab() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["financial", "payments"],
    queryFn: () => financialApi.listPayments(),
  });

  const payments = extractList(data);

  const columns: ColumnDef<Record<string, unknown>>[] = [
    { accessorKey: "id", header: "رقم الدفع" },
    { accessorKey: "invoice_id", header: "رقم الفاتورة" },
    { accessorKey: "amount", header: "المبلغ", cell: ({ row }) => formatCurrency(row.original.amount) },
    { accessorKey: "method", header: "طريقة الدفع" },
    { accessorKey: "status", header: "الحالة", cell: ({ row }) => statusBadge(row.original.status as string) },
    { accessorKey: "created_at", header: "التاريخ", cell: ({ row }) => formatDate(row.original.created_at as string) },
  ];

  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <Card>
      <CardContent className="pt-6">
        {!isLoading && payments.length === 0 ? (
          <EmptyState icon={CreditCard} title="لا توجد مدفوعات" description="لم يتم تسجيل أي مدفوعات بعد" />
        ) : (
          <DataTable columns={columns} data={payments as Record<string, unknown>[]} loading={isLoading} />
        )}
      </CardContent>
    </Card>
  );
}

function TransactionsTab() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["financial", "transactions"],
    queryFn: () => financialApi.listTransactions(),
  });

  const transactions = extractList(data);

  const columns: ColumnDef<Record<string, unknown>>[] = [
    { accessorKey: "id", header: "رقم العملية" },
    { accessorKey: "type", header: "النوع", cell: ({ row }) => <Badge variant={row.original.type === "credit" ? "success" : "destructive"}>{String(row.original.type ?? "-")}</Badge> },
    { accessorKey: "amount", header: "المبلغ", cell: ({ row }) => formatCurrency(row.original.amount) },
    { accessorKey: "description", header: "الوصف" },
    { accessorKey: "created_at", header: "التاريخ", cell: ({ row }) => formatDate(row.original.created_at as string) },
  ];

  if (error) return <ErrorDisplay onRetry={refetch} />;

  return (
    <Card>
      <CardContent className="pt-6">
        {!isLoading && transactions.length === 0 ? (
          <EmptyState icon={ArrowLeftRight} title="لا توجد معاملات" description="لم يتم تسجيل أي معاملات مالية بعد" />
        ) : (
          <DataTable columns={columns} data={transactions as Record<string, unknown>[]} loading={isLoading} />
        )}
      </CardContent>
    </Card>
  );
}

const tabComponents: Record<TabId, () => ReactElement> = {
  overview: OverviewTab,
  invoices: InvoicesTab,
  payments: PaymentsTab,
  transactions: TransactionsTab,
};

export function FinancialPage() {
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const ActiveComponent = tabComponents[activeTab];

  return (
    <div className="space-y-6">
      <PageHeader
        title="الإدارة المالية"
        description="إدارة الفواتير والمدفوعات والمعاملات المالية"
      />

      <div className="flex gap-1 rounded-lg bg-muted p-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <Button
              key={tab.id}
              variant={isActive ? "default" : "ghost"}
              size="sm"
              className="flex-1"
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </Button>
          );
        })}
      </div>

      <ActiveComponent />
    </div>
  );
}
