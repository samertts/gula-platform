import { useTranslation } from "react-i18next";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { resultsApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Input, Button, Select } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { Search, CheckCircle2 } from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { LabResult } from "@/types";
import { formatDateTime, getErrorMessage } from "@/lib/utils";
import { useDebounce } from "@/hooks/useDebounce";

const flagVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  normal: "success",
  high: "warning",
  low: "warning",
  H: "warning",
  L: "warning",
  critical_high: "destructive",
  critical_low: "destructive",
  critical: "destructive",
};

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  verified: "success",
  pending: "warning",
  pending_verification: "warning",
  rejected: "destructive",
};

export function ResultsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [category, setCategory] = useState("");
  const [abnormal, setAbnormal] = useState("");
  const [toast, setToast] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["results", debouncedSearch, category, abnormal],
    queryFn: () =>
      resultsApi.list({
        health_id: debouncedSearch || undefined,
        category: category || undefined,
        is_abnormal: abnormal === "yes" ? true : abnormal === "no" ? false : undefined,
        limit: 100,
      }),
  });

  const showToast = (kind: "success" | "error", message: string) => {
    setToast({ kind, message });
    window.setTimeout(() => setToast(null), 4000);
  };

  const verifyMutation = useMutation({
    mutationFn: (id: number) => resultsApi.verify(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["results"] });
      showToast("success", t("result.verified"));
    },
    onError: (err) => showToast("error", getErrorMessage(err)),
  });

  const results = data?.results || data?.items || [];

  const canVerify = (row: LabResult) => !row.verified_at && row.status !== "verified";

  const columns: ColumnDef<LabResult>[] = [
    { accessorKey: "id", header: t("result.id") },
    { accessorKey: "order_id", header: t("result.orderId") },
    { accessorKey: "test_name", header: t("result.testName") },
    {
      accessorKey: "value",
      header: t("result.value"),
      cell: ({ row }) => row.original.value ?? row.original.value_text ?? "-",
    },
    {
      accessorKey: "flag",
      header: t("result.flag"),
      cell: ({ row }) => {
        const flag = row.original.flag;
        return flag ? (
          <Badge variant={flagVariant[flag] || "secondary"}>{flag}</Badge>
        ) : (
          <Badge variant="outline">-</Badge>
        );
      },
    },
    {
      accessorKey: "status",
      header: t("result.status"),
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status || "pending"] || "secondary"}>
          {row.original.status || "pending"}
        </Badge>
      ),
    },
    {
      accessorKey: "created_at",
      header: t("result.createdAt"),
      cell: ({ row }) => formatDateTime(row.original.created_at),
    },
    {
      id: "actions",
      header: t("common.actions"),
      cell: ({ row }) => (
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => verifyMutation.mutate(row.original.id)}
            disabled={!canVerify(row.original)}
            title={t("result.verify")}
          >
            <CheckCircle2 className="h-4 w-4" />
            {t("result.verify")}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={t("result.title")} description={t("result.subtitle")} />

      {toast && (
        <div
          className={
            toast.kind === "success"
              ? "rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-700 dark:bg-green-950 dark:text-green-300"
              : "rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300"
          }
          role="status"
        >
          {toast.message}
        </div>
      )}

      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={results}
            loading={isLoading}
            error={isError ? (error as Error) : null}
            onRetry={() => refetch()}
            toolbar={
              <div className="flex w-full flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <div className="relative">
                    <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      placeholder={t("result.searchHealthId")}
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className="ps-9 w-64"
                    />
                  </div>
                  <Select
                    options={[
                      { value: "hematology", label: t("result.category.hematology") },
                      { value: "biochemistry", label: t("result.category.biochemistry") },
                      { value: "immunology", label: t("result.category.immunology") },
                      { value: "microbiology", label: t("result.category.microbiology") },
                      { value: "urinalysis", label: t("result.category.urinalysis") },
                      { value: "coagulation", label: t("result.category.coagulation") },
                    ]}
                    placeholder={t("result.allCategories")}
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-40"
                  />
                  <Select
                    options={[
                      { value: "yes", label: t("result.abnormalOnly") },
                      { value: "no", label: t("result.normalOnly") },
                    ]}
                    placeholder={t("result.allFlags")}
                    value={abnormal}
                    onChange={(e) => setAbnormal(e.target.value)}
                    className="w-40"
                  />
                </div>
              </div>
            }
          />
        </CardContent>
      </Card>
    </div>
  );
}
