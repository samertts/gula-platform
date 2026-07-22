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
import { User, Phone, MapPin, Calendar, Hash, Stethoscope } from "lucide-react";
import { getGenderLabel } from "@/lib/utils";

interface FhirPatientResource {
  resourceType: string;
  id: string;
  identifier?: { system?: string; value?: string }[];
  name?: { family?: string; given?: string[]; text?: string }[];
  gender?: string;
  birthDate?: string;
  telecom?: { system?: string; value?: string; use?: string }[];
  address?: { line?: string[]; city?: string; state?: string }[];
  generalPractitioner?: { reference?: string; display?: string }[];
  meta?: { versionId?: string; lastUpdated?: string };
}

function DetailRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div className="flex items-start gap-3 py-3 border-b last:border-0">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-sm font-medium break-words">{value || "—"}</p>
      </div>
    </div>
  );
}

function PatientSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex items-start gap-3 py-3 border-b last:border-0">
          <div className="h-8 w-8 rounded-full bg-muted animate-pulse" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-16 bg-muted animate-pulse rounded" />
            <div className="h-4 w-32 bg-muted animate-pulse rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function FhirPatientPage() {
  const [patientId, setPatientId] = useState("");
  const [searchId, setSearchId] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["fhir-patient", searchId],
    queryFn: () => complianceApi.fhirPatient(Number(searchId)) as Promise<FhirPatientResource>,
    enabled: !!searchId,
  });

  const patient = data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="مورد المريض FHIR"
        description="عرض بيانات المريض بتنسيق FHIR"
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            البحث عن مريض
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Input
              placeholder="أدخل رقم المريض..."
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && setSearchId(patientId.trim())}
            />
            <button
              onClick={() => setSearchId(patientId.trim())}
              disabled={!patientId.trim()}
              className="inline-flex h-10 shrink-0 items-center justify-center rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              بحث
            </button>
          </div>
        </CardContent>
      </Card>

      {isLoading && (
        <Card>
          <CardHeader>
            <CardTitle>بيانات المريض</CardTitle>
          </CardHeader>
          <CardContent>
            <PatientSkeleton />
          </CardContent>
        </Card>
      )}

      {error && <ErrorDisplay onRetry={() => refetch()} />}

      {!searchId && !isLoading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <User className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">أدخل رقم المريض للبحث</p>
          </CardContent>
        </Card>
      )}

      {patient && !isLoading && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              {patient.name?.[0]?.text || patient.name?.[0]?.given?.join(" ") || "مريض"}
              <Badge variant="outline" className="mr-2 text-xs">
                المعرف: {patient.id}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-0 md:grid-cols-2">
              <DetailRow
                icon={User}
                label="الاسم"
                value={patient.name?.[0]?.text || patient.name?.[0]?.given?.join(" ") || ""}
              />
              <DetailRow
                icon={Calendar}
                label="الجنس"
                value={getGenderLabel(patient.gender)}
              />
              <DetailRow
                icon={Calendar}
                label="تاريخ الميلاد"
                value={patient.birthDate || "—"}
              />
              <DetailRow
                icon={Hash}
                label="المعرفات"
                value={
                  patient.identifier
                    ?.map((id) => `[${id.system}] ${id.value}`)
                    .join(", ") || null
                }
              />
              <DetailRow
                icon={Phone}
                label="جهات الاتصال"
                value={
                  patient.telecom
                    ?.map((t) => `${t.system}: ${t.value}`)
                    .join(", ") || null
                }
              />
              <DetailRow
                icon={MapPin}
                label="العنوان"
                value={
                  patient.address
                    ?.map(
                      (a) =>
                        [a.line?.join(", "), a.city, a.state]
                          .filter(Boolean)
                          .join(" - ")
                    )
                    .join(" | ") || null
                }
              />
              {patient.generalPractitioner && patient.generalPractitioner.length > 0 && (
                <DetailRow
                  icon={Stethoscope}
                  label="الطبيب العام"
                  value={patient.generalPractitioner
                    ?.map((gp) => gp.display || gp.reference || "")
                    .join(", ") || null}
                />
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
