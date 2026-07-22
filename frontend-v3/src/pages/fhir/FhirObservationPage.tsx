import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { complianceApi } from "@/api/endpoints";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Badge,
} from "@/components/ui";
import {
  PageHeader,
  ErrorDisplay,
} from "@/components/shared/PageComponents";
import { FlaskConical, Calendar, User, Activity } from "lucide-react";
import { formatDateTime } from "@/lib/utils";

interface FhirObservationResource {
  resourceType: string;
  id: string;
  status?: string;
  code?: { coding?: { code?: string; display?: string; system?: string }[]; text?: string };
  subject?: { reference?: string; type?: string };
  effectiveDateTime?: string;
  issued?: string;
  performer?: { reference?: string; display?: string }[];
  valueQuantity?: { value?: number; unit?: string };
  valueString?: string;
  valueCodeableConcept?: { coding?: { code?: string; display?: string }[]; text?: string };
  referenceRange?: {
    low?: { value?: number };
    high?: { value?: number };
    text?: string;
  }[];
  interpretation?: { coding?: { code?: string; display?: string }[] }[];
  meta?: { versionId?: string; lastUpdated?: string };
}

function FlagBadge({ flag }: { flag: string | null | undefined }) {
  if (!flag) return null;
  const variant =
    flag === "normal" || flag === "N"
      ? "success"
      : flag === "high" || flag === "H"
        ? "warning"
        : flag === "low" || flag === "L"
          ? "secondary"
          : flag === "critical"
            ? "destructive"
            : "default";
  return <Badge variant={variant}>{flag}</Badge>;
}

function ObservationSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-start gap-3 py-3 border-b last:border-0">
          <div className="h-8 w-8 rounded-full bg-muted animate-pulse" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-20 bg-muted animate-pulse rounded" />
            <div className="h-4 w-40 bg-muted animate-pulse rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function FhirObservationPage() {
  const [orderId, setOrderId] = useState("");
  const [searchId, setSearchId] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["fhir-observation", searchId],
    queryFn: () => complianceApi.fhirObservation(Number(searchId)) as unknown as Promise<FhirObservationResource>,
    enabled: !!searchId,
  });

  const observation = data;
  const flag = observation?.interpretation?.[0]?.coding?.[0]?.code || null;
  const value =
    observation?.valueQuantity
      ? `${observation.valueQuantity.value} ${observation.valueQuantity.unit || ""}`.trim()
      : observation?.valueString || observation?.valueCodeableConcept?.text || "—";
  const refRange = observation?.referenceRange?.[0];

  return (
    <div className="space-y-6">
      <PageHeader
        title="مورد الملاحظة FHIR"
        description="عرض نتائج المختبر بتنسيق FHIR Observation"
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FlaskConical className="h-5 w-5" />
            البحث عن ملاحظة
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Input
              placeholder="أدخل رقم الطلب..."
              value={orderId}
              onChange={(e) => setOrderId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && setSearchId(orderId.trim())}
            />
            <button
              onClick={() => setSearchId(orderId.trim())}
              disabled={!orderId.trim()}
              className="inline-flex h-10 shrink-0 items-center justify-center rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              بحث
            </button>
          </div>
        </CardContent>
      </Card>

      {isLoading && (
        <Card>
          <CardContent>
            <ObservationSkeleton />
          </CardContent>
        </Card>
      )}

      {error && <ErrorDisplay onRetry={() => refetch()} />}

      {!searchId && !isLoading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FlaskConical className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">أدخل رقم الطلب للبحث</p>
          </CardContent>
        </Card>
      )}

      {observation && !isLoading && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                {observation.code?.text || observation.code?.coding?.[0]?.display || "ملاحظة"}
                <FlagBadge flag={flag} />
                <Badge variant="outline" className="text-xs">
                  {observation.status}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-0 md:grid-cols-2">
                <div className="flex items-start gap-3 py-3 border-b md:border-b-0">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                    <FlaskConical className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">القيمة</p>
                    <p className="text-lg font-bold">{value}</p>
                  </div>
                </div>
                {refRange && (
                  <div className="flex items-start gap-3 py-3 border-b md:border-b-0">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                      <Activity className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">النطاق المرجعي</p>
                      <p className="text-sm font-medium">
                        {refRange.low?.value ?? "?"} - {refRange.high?.value ?? "?"}
                      </p>
                    </div>
                  </div>
                )}
                <div className="flex items-start gap-3 py-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">تاريخ الإصدار</p>
                    <p className="text-sm font-medium">
                      {observation.issued ? formatDateTime(observation.issued) : "—"}
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 py-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                    <User className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">المريض</p>
                    <p className="text-sm font-medium">
                      {observation.subject?.reference?.replace("Patient/", "") || "—"}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">البيانات الخام (JSON)</CardTitle>
            </CardHeader>
            <CardContent>
              <pre
                className="overflow-auto rounded-lg bg-muted p-4 text-xs max-h-80"
                dir="ltr"
              >
                <code>{JSON.stringify(observation, null, 2)}</code>
              </pre>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
