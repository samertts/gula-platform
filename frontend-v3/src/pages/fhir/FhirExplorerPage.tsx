import { useState, useCallback } from "react";
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
  LoadingSpinner,
  ErrorDisplay,
} from "@/components/shared/PageComponents";
import { Search, FileJson } from "lucide-react";

const RESOURCE_TYPES = [
  "Patient",
  "Observation",
  "DiagnosticReport",
  "Encounter",
  "Condition",
  "MedicationRequest",
  "Immunization",
  "AllergyIntolerance",
  "Composition",
  "DocumentReference",
  "Procedure",
  "CarePlan",
  "Bundle",
] as const;

type ResourceType = (typeof RESOURCE_TYPES)[number];

function fhirLookup(resourceType: ResourceType, id: string) {
  switch (resourceType) {
    case "Patient":
      return complianceApi.fhirPatient(Number(id));
    case "Observation":
      return complianceApi.fhirObservation(Number(id));
    case "DiagnosticReport":
      return complianceApi.fhirDiagnosticReport(Number(id));
    default:
      return complianceApi.fhirPatient(Number(id));
  }
}

export function FhirExplorerPage() {
  const [resourceType, setResourceType] = useState<ResourceType>("Patient");
  const [resourceId, setResourceId] = useState("");
  const [searchId, setSearchId] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["fhir-explorer", resourceType, searchId],
    queryFn: () => fhirLookup(resourceType, searchId),
    enabled: !!searchId,
  });

  const handleSearch = useCallback(() => {
    if (resourceId.trim()) {
      setSearchId(resourceId.trim());
    }
  }, [resourceId]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="مستعرض FHIR"
        description="استعراض موارد FHIR"
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            بحث في مورد FHIR
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-3">
            <select
              className="flex h-10 w-full sm:w-48 rounded-lg border border-input bg-background px-3 py-2 text-sm"
              dir="rtl"
              value={resourceType}
              onChange={(e) => setResourceType(e.target.value as ResourceType)}
            >
              {RESOURCE_TYPES.map((rt) => (
                <option key={rt} value={rt}>
                  {rt}
                </option>
              ))}
            </select>
            <Input
              placeholder="أدخل معرف المورد..."
              value={resourceId}
              onChange={(e) => setResourceId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="flex-1"
            />
            <button
              onClick={handleSearch}
              disabled={!resourceId.trim()}
              className="inline-flex h-10 items-center justify-center rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              بحث
            </button>
          </div>
        </CardContent>
      </Card>

      {!searchId && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FileJson className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              اختر نوع المورد وأدخل المعرف للبدء
            </p>
          </CardContent>
        </Card>
      )}

      {isLoading && <LoadingSpinner />}

      {error && <ErrorDisplay onRetry={() => refetch()} />}

      {data && !isLoading && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileJson className="h-5 w-5" />
              <span dir="ltr">{resourceType}/{searchId}</span>
              <Badge variant="secondary" className="mr-2">
                {(data as Record<string, unknown>)?.resourceType as string}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre
              className="overflow-auto rounded-lg bg-muted p-4 text-sm max-h-[600px]"
              dir="ltr"
            >
              <code>{JSON.stringify(data, null, 2)}</code>
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
