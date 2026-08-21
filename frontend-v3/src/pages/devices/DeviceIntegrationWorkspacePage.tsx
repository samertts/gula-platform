import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Cable,
  CheckCircle2,
  CircleOff,
  Clock3,
  Cpu,
  FileOutput,
  FlaskConical,
  Gauge,
  Laptop,
  Link2,
  Loader2,
  Monitor,
  Network,
  Printer,
  Radio,
  RefreshCw,
  Router,
  Search,
  Server,
  ShieldCheck,
  Stethoscope,
  Tags,
  XCircle,
} from "lucide-react";
import { deviceIntegrationApi } from "@/api/endpoints";
import { useAuth } from "@/contexts/AuthContext";
import { PageHeader } from "@/components/shared/PageComponents";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type {
  DeviceIntegrationCategory,
  DeviceIntegrationConnectorRecord,
  DeviceIntegrationEventRecord,
  DeviceIntegrationPrinterJob,
  DeviceIntegrationProtocolDescriptor,
  DeviceIntegrationProtocolProfileRecord,
  DeviceIntegrationRecord,
  DeviceIntegrationSimulatorDescriptor,
  DeviceIntegrationStatus,
  DeviceIntegrationSummary,
  DeviceGatewayAlertRecord,
  DeviceGatewayMonitoringSnapshot,
  WearableBaselineSummary,
} from "@/types";

const SYNTHETIC_DEVICES: DeviceIntegrationRecord[] = [
  {
    id: 1,
    device_uid: "VITAL-BP-001",
    display_name: "جهاز ضغط المريض — جناح الطوارئ",
    category: "medical_measurement",
    vendor: "GULA Synthetic",
    model: "BP-SIM-01",
    serial_number: "SYN-BP-001",
    protocol: "FHIR_Device",
    transport: "Bluetooth",
    endpoint: "sim://bluetooth/vitals/bp-001",
    status: "connected",
    simulation_only: true,
    last_seen_at: "2026-08-15T08:42:00Z",
    capabilities: { metrics: ["systolic", "diastolic", "pulse"] },
    created_at: "2026-08-01T09:00:00Z",
    updated_at: "2026-08-15T08:42:00Z",
  },
  {
    id: 2,
    device_uid: "MONITOR-ECG-002",
    display_name: "مراقب ECG وSpO₂ — العناية الحرجة",
    category: "patient_monitor",
    vendor: "GULA Synthetic",
    model: "MON-SIM-02",
    serial_number: "SYN-ECG-002",
    protocol: "FHIR_Device",
    transport: "WiFi",
    endpoint: "sim://wifi/monitor/ecg-002",
    status: "connected",
    simulation_only: true,
    last_seen_at: "2026-08-15T08:39:00Z",
    capabilities: { metrics: ["ecg", "spo2", "temperature", "respiratory_rate"] },
    created_at: "2026-08-01T09:05:00Z",
    updated_at: "2026-08-15T08:39:00Z",
  },
  {
    id: 3,
    device_uid: "MINDRAY-BC-5380-003",
    display_name: "محلل دموي — مختبر أمراض الدم",
    category: "laboratory_analyzer",
    vendor: "GULA Synthetic",
    model: "ANALYZER-SIM-BC",
    serial_number: "SYN-BC-003",
    protocol: "HL7v2_MLLP",
    transport: "MLLP",
    endpoint: "sim://mllp/lab/2575",
    status: "connected",
    simulation_only: true,
    last_seen_at: "2026-08-15T08:36:00Z",
    capabilities: { domains: ["hematology", "qc"], message_types: ["ORU^R01", "ACK"] },
    created_at: "2026-08-01T09:10:00Z",
    updated_at: "2026-08-15T08:36:00Z",
  },
  {
    id: 4,
    device_uid: "GENEXPERT-ASTM-004",
    display_name: "محلل PCR — وحدة الجزيئات",
    category: "laboratory_analyzer",
    vendor: "GULA Synthetic",
    model: "PCR-SIM-X",
    serial_number: "SYN-PCR-004",
    protocol: "ASTM",
    transport: "TCP",
    endpoint: "sim://astm/lab/5000",
    status: "error",
    simulation_only: true,
    last_seen_at: "2026-08-15T07:54:00Z",
    capabilities: { domains: ["molecular", "qc"], framing: "ENQ/ACK" },
    created_at: "2026-08-01T09:15:00Z",
    updated_at: "2026-08-15T07:54:00Z",
  },
  {
    id: 5,
    device_uid: "DICOM-PACS-005",
    display_name: "بوابة التصوير وDICOM Worklist",
    category: "imaging",
    vendor: "GULA Synthetic",
    model: "PACS-SIM-01",
    serial_number: "SYN-PACS-005",
    protocol: "DICOM",
    transport: "HTTP",
    endpoint: "sim://dicom/pacs/worklist",
    status: "connected",
    simulation_only: true,
    last_seen_at: "2026-08-15T08:31:00Z",
    capabilities: { services: ["MWL", "C-FIND", "DICOMweb"], ae_title: "GULA_SIM" },
    created_at: "2026-08-01T09:20:00Z",
    updated_at: "2026-08-15T08:31:00Z",
  },
  {
    id: 6,
    device_uid: "ZEBRA-ZPL-006",
    display_name: "طابعة ملصقات العينات — الاستقبال",
    category: "printer",
    vendor: "GULA Synthetic",
    model: "ZPL-SIM-01",
    serial_number: "SYN-ZPL-006",
    protocol: "ZPL",
    transport: "TCP",
    endpoint: "sim://printer/zpl/9100",
    status: "connected",
    simulation_only: true,
    last_seen_at: "2026-08-15T08:40:00Z",
    printer_profile: { dpi: 203, label_size: "50x25mm", languages: ["ZPL"] },
    created_at: "2026-08-01T09:25:00Z",
    updated_at: "2026-08-15T08:40:00Z",
  },
  {
    id: 7,
    device_uid: "REPORT-PDF-007",
    display_name: "طابـعة تقارير المختبر — الإدارة",
    category: "printer",
    vendor: "GULA Synthetic",
    model: "PDF-QUEUE-SIM",
    serial_number: "SYN-PDF-007",
    protocol: "PDF",
    transport: "HTTP",
    endpoint: "sim://printer/pdf/queue",
    status: "maintenance",
    simulation_only: true,
    last_seen_at: "2026-08-14T16:10:00Z",
    printer_profile: { page_size: "A4", color: false, languages: ["PDF"] },
    created_at: "2026-08-01T09:30:00Z",
    updated_at: "2026-08-14T16:10:00Z",
  },
  {
    id: 8,
    device_uid: "WS-LAB-008",
    display_name: "محطة عمل فني المختبر",
    category: "workstation",
    vendor: "GULA Synthetic",
    model: "WS-SIM-01",
    serial_number: "SYN-WS-008",
    protocol: "TCP_IP",
    transport: "WiFi",
    endpoint: "sim://workstation/lab-008",
    status: "connected",
    simulation_only: true,
    last_seen_at: "2026-08-15T08:41:00Z",
    capabilities: { roles: ["operator_console", "barcode_input"] },
    created_at: "2026-08-01T09:35:00Z",
    updated_at: "2026-08-15T08:41:00Z",
  },
  {
    id: 9,
    device_uid: "BARCODE-USB-009",
    display_name: "قارئ باركود — سحب العينات",
    category: "barcode_scanner",
    vendor: "GULA Synthetic",
    model: "SCANNER-SIM",
    serial_number: "SYN-SCAN-009",
    protocol: "USB_Serial",
    transport: "USB",
    endpoint: "sim://usb/scanner/009",
    status: "disconnected",
    simulation_only: true,
    last_seen_at: "2026-08-15T06:20:00Z",
    capabilities: { symbologies: ["Code128", "QR", "DataMatrix"] },
    created_at: "2026-08-01T09:40:00Z",
    updated_at: "2026-08-15T06:20:00Z",
  },
  {
    id: 10,
    device_uid: "NET-GATEWAY-010",
    display_name: "بوابة شبكة الأجهزة المعزولة",
    category: "network",
    vendor: "GULA Synthetic",
    model: "SEGMENT-SIM",
    serial_number: "SYN-NET-010",
    protocol: "TCP_IP",
    transport: "TCP",
    endpoint: "sim://network/medical-segment",
    status: "connected",
    simulation_only: true,
    last_seen_at: "2026-08-15T08:43:00Z",
    capabilities: { segment: "medical-device-vlan", allowlisted_adapters: 4 },
    created_at: "2026-08-01T09:45:00Z",
    updated_at: "2026-08-15T08:43:00Z",
  },
];

const SYNTHETIC_PROTOCOLS: DeviceIntegrationProtocolDescriptor[] = [
  { key: "HL7v2_MLLP", label: "HL7 v2 over MLLP", family: "clinical_messaging", transports: ["MLLP", "TCP"], intended_categories: ["laboratory_analyzer", "patient_monitor"], production_requirement: "Adapter خادمي مع ACK/NAK وallowlist للشبكة.", simulation_supported: true },
  { key: "ASTM", label: "ASTM LIS2-A2", family: "laboratory_messaging", transports: ["TCP", "Serial"], intended_categories: ["laboratory_analyzer"], production_requirement: "Adapter خاص بالمحلل وإدارة ENQ/ACK وmapping للحقول.", simulation_supported: true },
  { key: "DICOM", label: "DICOM / Worklist", family: "imaging", transports: ["TCP", "HTTP"], intended_categories: ["imaging"], production_requirement: "بوابة PACS مع AE Title وTLS والتحقق من المطابقة.", simulation_supported: true },
  { key: "FHIR_Device", label: "FHIR Device + Observation", family: "health_data", transports: ["HTTP"], intended_categories: ["medical_measurement", "patient_monitor", "laboratory_analyzer"], production_requirement: "عميل FHIR موثق مع profiles وprovenance وموافقة.", simulation_supported: true },
  { key: "TCP_IP", label: "TCP/IP", family: "network_transport", transports: ["TCP"], intended_categories: ["network", "laboratory_analyzer", "printer"], production_requirement: "بوابة ثابتة مع timeout وparser ووجهات مسموحة.", simulation_supported: true },
  { key: "USB_Serial", label: "USB / RS-232", family: "local_transport", transports: ["USB", "Serial"], intended_categories: ["laboratory_analyzer", "barcode_scanner", "printer"], production_requirement: "Agent محلي بصلاحيات OS وقناة مشفرة للمنصة.", simulation_supported: true },
  { key: "Bluetooth", label: "Bluetooth LE", family: "local_transport", transports: ["Bluetooth"], intended_categories: ["medical_measurement", "patient_monitor"], production_requirement: "Agent محلي وسياسة pairing والتحقق من الجهاز.", simulation_supported: true },
  { key: "WiFi", label: "Wi-Fi transport", family: "network_transport", transports: ["WiFi", "TCP", "HTTP"], intended_categories: ["medical_measurement", "patient_monitor", "workstation"], production_requirement: "شبكة طبية مجزأة؛ Wi-Fi ليس بروتوكول رسالة وحده.", simulation_supported: true },
  { key: "ZPL", label: "ZPL barcode labels", family: "printing", transports: ["TCP", "USB"], intended_categories: ["printer"], production_requirement: "قوالب مسموحة وpreview وسجل تدقيق.", simulation_supported: true },
  { key: "IPL", label: "IPL barcode labels", family: "printing", transports: ["TCP", "USB"], intended_categories: ["printer"], production_requirement: "Adapter خاص بالطابعة والتحقق من القالب.", simulation_supported: true },
  { key: "PDF", label: "PDF reports", family: "printing", transports: ["HTTP", "File"], intended_categories: ["printer", "workstation"], production_requirement: "طابور تقارير خادمي وصلاحيات وصول.", simulation_supported: true },
];

const SYNTHETIC_EVENTS: DeviceIntegrationEventRecord[] = [
  { id: 1, device_uid: "MINDRAY-BC-5380-003", event_type: "message_received", direction: "inbound", severity: "info", message_type: "ORU^R01", summary: "تم استقبال نتيجة اصطناعية وتحويلها إلى مسار موحّد", correlation_id: "sim-evt-001", safe_metadata: { simulation_only: true, parser: "HL7v2_MLLP" }, occurred_at: "2026-08-15T08:36:00Z" },
  { id: 2, device_uid: "GENEXPERT-ASTM-004", event_type: "connection_error", direction: "system", severity: "error", summary: "فشل probe المحاكي؛ لا يوجد Adapter فعلي متصل", correlation_id: "sim-evt-002", safe_metadata: { simulation_only: true, retryable: true }, occurred_at: "2026-08-15T07:54:00Z" },
  { id: 3, device_uid: "ZEBRA-ZPL-006", event_type: "print_job_simulated", direction: "outbound", severity: "info", summary: "اكتملت محاكاة طباعة ملصق ZPL", correlation_id: "sim-evt-003", safe_metadata: { simulation_only: true, label_count: 3 }, occurred_at: "2026-08-15T08:40:00Z" },
  { id: 4, device_uid: "DICOM-PACS-005", event_type: "worklist_sync", direction: "inbound", severity: "info", summary: "تمت مزامنة قائمة عمل DICOM اصطناعية", correlation_id: "sim-evt-004", safe_metadata: { simulation_only: true, records: 6 }, occurred_at: "2026-08-15T08:31:00Z" },
];

const SYNTHETIC_JOBS: DeviceIntegrationPrinterJob[] = [
  { id: 1, device_uid: "ZEBRA-ZPL-006", document_type: "specimen_label", printer_language: "ZPL", label_count: 3, status: "simulated_success", simulation_only: true, safe_metadata: { template_key: "specimen-default" }, created_at: "2026-08-15T08:40:00Z", completed_at: "2026-08-15T08:40:01Z" },
  { id: 2, device_uid: "REPORT-PDF-007", document_type: "report", printer_language: "PDF", label_count: 1, status: "queued", simulation_only: true, safe_metadata: { template_key: "lab-report-a4" }, created_at: "2026-08-15T08:15:00Z" },
];

const SYNTHETIC_CONNECTORS: DeviceIntegrationConnectorRecord[] = [
  { id: 1, connector_uid: "CONN-HL7-001", display_name: "HL7 محلل الدم", device_uid: "MINDRAY-BC-5380-003", protocol: "HL7v2_MLLP", transport: "MLLP", mode: "simulated", status: "healthy", contract_version: "v1", gateway_ref: "sim://connector/hl7-001", config_safe: { ack_strategy: "simulated_ack", timeout_seconds: 30 }, capability_manifest: { message_types: ["ORU^R01", "ACK"] }, last_heartbeat_at: "2026-08-15T08:36:00Z", enabled: true, simulation_only: true, created_at: "2026-08-01T09:10:00Z", updated_at: "2026-08-15T08:36:00Z" },
  { id: 2, connector_uid: "CONN-ASTM-002", display_name: "ASTM محلل PCR", device_uid: "GENEXPERT-ASTM-004", protocol: "ASTM", transport: "TCP", mode: "gateway_pending", status: "error", contract_version: "v1", gateway_ref: "gateway://pending/CONN-ASTM-002", config_safe: { framing: "ENQ/ACK", timeout_seconds: 45 }, capability_manifest: { result_records: true }, last_error: "simulated adapter failure", enabled: true, simulation_only: true, created_at: "2026-08-01T09:15:00Z", updated_at: "2026-08-15T07:54:00Z" },
  { id: 3, connector_uid: "CONN-DICOM-003", display_name: "DICOM Worklist Gateway", device_uid: "DICOM-PACS-005", protocol: "DICOM", transport: "HTTP", mode: "simulated", status: "healthy", contract_version: "v1", gateway_ref: "sim://connector/dicom-003", config_safe: { service: "C-FIND", ae_title: "GULA_SIM" }, capability_manifest: { worklist: true, dicomweb: true }, last_heartbeat_at: "2026-08-15T08:31:00Z", enabled: true, simulation_only: true, created_at: "2026-08-01T09:20:00Z", updated_at: "2026-08-15T08:31:00Z" },
  { id: 4, connector_uid: "CONN-ZPL-004", display_name: "ZPL Label Gateway", device_uid: "ZEBRA-ZPL-006", protocol: "ZPL", transport: "TCP", mode: "simulated", status: "healthy", contract_version: "v1", gateway_ref: "sim://connector/zpl-004", config_safe: { template_allowlist: ["specimen-default"] }, capability_manifest: { preview: true, label_languages: ["ZPL"] }, last_heartbeat_at: "2026-08-15T08:40:00Z", enabled: true, simulation_only: true, created_at: "2026-08-01T09:25:00Z", updated_at: "2026-08-15T08:40:00Z" },
];

const SYNTHETIC_ALERTS: DeviceGatewayAlertRecord[] = [
  { id: 1, gateway_ref: "gateway-lab-sim-01", alert_key: "outbox_oldest_age", severity: "warning", status: "open", title: "تأخير Outbox مرتفع", summary: "أقدم رسالة في Outbox تجاوزت حد التنبيه.", metric_key: "outbox_oldest_age_seconds", current_value: 412, threshold_value: 300, first_seen_at: "2026-08-15T08:20:00Z", last_seen_at: "2026-08-15T08:42:00Z", correlation_id: "sim-alert-001", simulation_only: true, safe_metadata: { simulation_only: true } },
  { id: 2, gateway_ref: "gateway-lab-sim-02", alert_key: "disk_usage", severity: "critical", status: "acknowledged", title: "استهلاك القرص حرج", summary: "استهلاك قرص Gateway تجاوز الحد الحرج.", metric_key: "disk_used_percent", current_value: 96.4, threshold_value: 95, first_seen_at: "2026-08-15T07:55:00Z", last_seen_at: "2026-08-15T08:41:00Z", acknowledged_at: "2026-08-15T08:42:00Z", acknowledged_by: 1, correlation_id: "sim-alert-002", simulation_only: true, safe_metadata: { simulation_only: true } },
];

const SYNTHETIC_BASELINE_SUMMARY: WearableBaselineSummary = {
  patient_id: 1,
  metric_code: "systolic_bp",
  measurement_count: 21,
  latest: { value: 132, unit: "mmHg", measured_at: "2026-08-15T08:40:00Z", quality_score: 0.96, source: "fitbit" },
  baseline: { status: "ready", median: 128, mad: 5, lower_bound: 113, upper_bound: 143, confidence: 0.86, generated_at: "2026-08-15T08:42:00Z" },
  evaluation: { is_anomaly: false, severity: "normal", deviation_score: 0.54, confidence: 0.86, explanation: "القراءة ضمن النطاق الشخصي المتعلم؛ يلزم تفسيرها مع السياق السريري.", requires_clinician_review: false, advisory_only: true },
};

const SYNTHETIC_MONITORING: DeviceGatewayMonitoringSnapshot = {
  gateway_count: 2,
  healthy_gateway_count: 1,
  degraded_gateway_count: 1,
  offline_gateway_count: 0,
  latest_metric: { id: 2, gateway_ref: "gateway-lab-sim-02", gateway_status: "degraded", gateway_version: "sim-gateway-0.4.0", outbox_pending_count: 18, outbox_oldest_age_seconds: 412, outbox_retry_count: 4, outbox_dead_letter_count: 1, disk_used_percent: 96.4, disk_free_bytes: 4294967296, worker_last_heartbeat_at: "2026-08-15T08:42:00Z", worker_lag_seconds: 138, transport_latency_ms: 2640, captured_at: "2026-08-15T08:42:00Z", simulation_only: true, safe_metadata: { simulation_only: true } },
  open_alert_count: 2,
  critical_alert_count: 1,
  alerts: SYNTHETIC_ALERTS,
  thresholds: { outbox_oldest_age_warning_seconds: 300, outbox_oldest_age_critical_seconds: 900, disk_used_warning_percent: 85, disk_used_critical_percent: 95, dead_letter_warning_count: 1, worker_lag_warning_seconds: 120, transport_latency_warning_ms: 2000 },
  simulation_only: true,
};

const SYNTHETIC_PROFILES: DeviceIntegrationProtocolProfileRecord[] = [
  { id: 1, profile_key: "hl7.oru.r01.v1", protocol: "HL7v2_MLLP", version: "v1", message_type: "ORU^R01", framing: "MLLP", ack_strategy: "ACK/NAK", encoding: "UTF-8", mapping_schema: { result_id: "OBR-3", value: "OBX-5" }, validation_rules: { required_segments: ["MSH", "PID", "OBR", "OBX"] }, simulator_key: "hl7v2.oru.r01", status: "validated", simulation_only: true, created_by: 1, created_at: "2026-08-01T09:10:00Z", updated_at: "2026-08-15T08:36:00Z" },
  { id: 2, profile_key: "astm.result.v1", protocol: "ASTM", version: "v1", message_type: "RESULT", framing: "ENQ/ACK", ack_strategy: "frame_ack", encoding: "ASCII", mapping_schema: { test_code: "R-3", result: "R-4" }, validation_rules: { required_records: ["H", "P", "O", "R", "L"] }, simulator_key: "astm.result", status: "draft", simulation_only: true, created_by: 1, created_at: "2026-08-01T09:15:00Z", updated_at: "2026-08-15T07:54:00Z" },
  { id: 3, profile_key: "dicom.mwl.v1", protocol: "DICOM", version: "v1", message_type: "C-FIND", framing: "DIMSE", ack_strategy: "status_code", encoding: "DICOM", mapping_schema: { accession: "AccessionNumber", modality: "Modality" }, validation_rules: { ae_title_required: true }, simulator_key: "dicom.worklist", status: "validated", simulation_only: true, created_by: 1, created_at: "2026-08-01T09:20:00Z", updated_at: "2026-08-15T08:31:00Z" },
];

const SYNTHETIC_SIMULATORS: DeviceIntegrationSimulatorDescriptor[] = [
  { key: "hl7v2.oru.r01", label: "HL7 v2 ORU^R01 result", protocol: "HL7v2_MLLP", family: "clinical_messaging", contract_summary: "MSH/ORU^R01 contract with ACK/NAK expectation", output: "safe result envelope metadata only", simulation_only: true },
  { key: "astm.result", label: "ASTM analyzer result", protocol: "ASTM", family: "laboratory_messaging", contract_summary: "ENQ/ACK frame sequence with result record", output: "safe analyzer result metadata only", simulation_only: true },
  { key: "dicom.worklist", label: "DICOM Modality Worklist", protocol: "DICOM", family: "imaging", contract_summary: "C-FIND worklist exchange without DICOM objects", output: "safe worklist transaction metadata only", simulation_only: true },
  { key: "fhir.device-observation", label: "FHIR Device and Observation envelope", protocol: "FHIR_Device", family: "health_data", contract_summary: "Device/Observation profile validation envelope", output: "resource type and profile metadata only", simulation_only: true },
  { key: "zpl.specimen-label", label: "ZPL specimen label", protocol: "ZPL", family: "printing", contract_summary: "allowlisted specimen label template", output: "label count and template metadata only", simulation_only: true },
  { key: "pdf.report", label: "PDF laboratory report", protocol: "PDF", family: "printing", contract_summary: "report render and queue contract", output: "document type and page metadata only", simulation_only: true },
];

const CATEGORY_LABELS: Record<DeviceIntegrationCategory, string> = {
  medical_measurement: "قياس طبي",
  patient_monitor: "مراقبة مريض",
  laboratory_analyzer: "محلل مختبري",
  imaging: "تصوير وPACS",
  printer: "طابعة",
  workstation: "محطة عمل",
  network: "شبكة",
  barcode_scanner: "قارئ باركود",
  other: "أخرى",
};

const STATUS_META: Record<DeviceIntegrationStatus, { label: string; variant: "success" | "warning" | "destructive" | "outline"; icon: typeof CheckCircle2 }> = {
  connected: { label: "متصل", variant: "success", icon: CheckCircle2 },
  disconnected: { label: "منفصل", variant: "outline", icon: CircleOff },
  error: { label: "خطأ", variant: "destructive", icon: XCircle },
  maintenance: { label: "صيانة", variant: "warning", icon: Clock3 },
  pending: { label: "قيد الإعداد", variant: "outline", icon: Loader2 },
};

const CONNECTOR_STATUS_META: Record<DeviceIntegrationConnectorRecord["status"], { label: string; variant: "success" | "warning" | "destructive" | "outline" }> = {
  healthy: { label: "سليم", variant: "success" },
  degraded: { label: "متدهور", variant: "warning" },
  offline: { label: "غير متاح", variant: "outline" },
  error: { label: "خطأ", variant: "destructive" },
  maintenance: { label: "صيانة", variant: "warning" },
  pending: { label: "بانتظار Gateway", variant: "outline" },
};

function syntheticSummary(): DeviceIntegrationSummary {
  const counts = SYNTHETIC_DEVICES.reduce<Record<string, number>>((acc, device) => {
    acc[device.category] = (acc[device.category] ?? 0) + 1;
    return acc;
  }, {});
  return {
    total: SYNTHETIC_DEVICES.length,
    connected: SYNTHETIC_DEVICES.filter((device) => device.status === "connected").length,
    disconnected: SYNTHETIC_DEVICES.filter((device) => device.status === "disconnected").length,
    error: SYNTHETIC_DEVICES.filter((device) => device.status === "error").length,
    maintenance: SYNTHETIC_DEVICES.filter((device) => device.status === "maintenance").length,
    pending: SYNTHETIC_DEVICES.filter((device) => device.status === "pending").length,
    simulation_only: SYNTHETIC_DEVICES.length,
    by_category: counts,
    recent_events: SYNTHETIC_EVENTS.length,
  };
}

function formatTime(value?: string) {
  if (!value) return "غير متاح";
  return new Intl.DateTimeFormat("ar-IQ", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function deviceIcon(category: DeviceIntegrationCategory) {
  const icons: Record<DeviceIntegrationCategory, typeof Stethoscope> = {
    medical_measurement: Gauge,
    patient_monitor: Monitor,
    laboratory_analyzer: FlaskConical,
    imaging: Radio,
    printer: Printer,
    workstation: Laptop,
    network: Network,
    barcode_scanner: Tags,
    other: Cpu,
  };
  return icons[category];
}

export function DeviceIntegrationWorkspacePage() {
  const { demoMode, user } = useAuth();
  const isInstitutional = Boolean(user?.lab_id && user.role !== "citizen");
  const [activeTab, setActiveTab] = useState<"overview" | "devices" | "connectors" | "protocols" | "profiles" | "simulators" | "events" | "printing" | "monitoring" | "chronic_care">("overview");
  const [devices, setDevices] = useState<DeviceIntegrationRecord[]>(SYNTHETIC_DEVICES);
  const [summary, setSummary] = useState<DeviceIntegrationSummary>(syntheticSummary());
  const [protocols, setProtocols] = useState<DeviceIntegrationProtocolDescriptor[]>(SYNTHETIC_PROTOCOLS);
  const [events, setEvents] = useState<DeviceIntegrationEventRecord[]>(SYNTHETIC_EVENTS);
  const [jobs, setJobs] = useState<DeviceIntegrationPrinterJob[]>(SYNTHETIC_JOBS);
  const [connectors, setConnectors] = useState<DeviceIntegrationConnectorRecord[]>(SYNTHETIC_CONNECTORS);
  const [profiles, setProfiles] = useState<DeviceIntegrationProtocolProfileRecord[]>(SYNTHETIC_PROFILES);
  const [simulators, setSimulators] = useState<DeviceIntegrationSimulatorDescriptor[]>(SYNTHETIC_SIMULATORS);
  const [monitoring, setMonitoring] = useState<DeviceGatewayMonitoringSnapshot>(SYNTHETIC_MONITORING);
  const [baselineSummary, setBaselineSummary] = useState<WearableBaselineSummary | null>(null);
  const [baselinePatientId, setBaselinePatientId] = useState("1");
  const [baselineMetric, setBaselineMetric] = useState("systolic_bp");
  const [baselineLoading, setBaselineLoading] = useState(false);
  const [alertActionId, setAlertActionId] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<"all" | DeviceIntegrationCategory>("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionUid, setActionUid] = useState<string | null>(null);
  const [error, setError] = useState("");

  const loadLive = async () => {
    if (demoMode || !isInstitutional) return;
    setLoading(true);
    setError("");
    try {
      const [summaryResponse, devicesResponse, protocolsResponse, eventsResponse, jobsResponse, connectorsResponse, profilesResponse, simulatorsResponse, monitoringResponse] = await Promise.all([
        deviceIntegrationApi.summary(),
        deviceIntegrationApi.list({ limit: 200 }),
        deviceIntegrationApi.protocols(),
        deviceIntegrationApi.events({ limit: 100 }),
        deviceIntegrationApi.printerJobs({ limit: 100 }),
        deviceIntegrationApi.connectors({ limit: 200 }),
        deviceIntegrationApi.protocolProfiles({ limit: 200 }),
        deviceIntegrationApi.simulators(),
        deviceIntegrationApi.monitoring(),
      ]);
      setSummary(summaryResponse);
      setDevices(devicesResponse.devices);
      setProtocols(protocolsResponse);
      setEvents(eventsResponse.events);
      setJobs(jobsResponse.jobs);
      setConnectors(connectorsResponse.connectors);
      setProfiles(profilesResponse.profiles);
      setSimulators(simulatorsResponse);
      setMonitoring(monitoringResponse);
    } catch {
      setError("تعذر تحميل بيانات الأجهزة من backend؛ لم يتم استبدال وضع live ببيانات اصطناعية.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isInstitutional) void loadLive();
  }, [demoMode, isInstitutional]);

  const loadBaselineSummary = async () => {
    const patientId = Number.parseInt(baselinePatientId, 10);
    if (!Number.isInteger(patientId) || patientId < 1) {
      setError("أدخل رقم مريض صحيحًا لتحميل baseline الاستشاري.");
      return;
    }
    setBaselineLoading(true);
    setError("");
    try {
      const result = demoMode
        ? { ...SYNTHETIC_BASELINE_SUMMARY, patient_id: patientId, metric_code: baselineMetric }
        : await deviceIntegrationApi.baselineSummary(patientId, baselineMetric, 28);
      setBaselineSummary(result);
    } catch {
      setBaselineSummary(null);
      setError("تعذر تحميل baseline للمريض؛ لم يتم إنشاء قرار علاجي تلقائي.");
    } finally {
      setBaselineLoading(false);
    }
  };

  const filteredDevices = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    return devices.filter((device) => {
      const matchesCategory = selectedCategory === "all" || device.category === selectedCategory;
      const matchesSearch = !normalized || `${device.device_uid} ${device.display_name} ${device.model ?? ""} ${device.protocol}`.toLowerCase().includes(normalized);
      return matchesCategory && matchesSearch;
    });
  }, [devices, search, selectedCategory]);

  const printerDevices = devices.filter((device) => device.category === "printer");

  if (!isInstitutional) {
    return (
      <div className="mx-auto max-w-3xl space-y-6" dir="rtl">
        <PageHeader title="مركز ربط الأجهزة" description="وحدة مؤسسية لإدارة الأجهزة والبوابات والمراقبة." />
        <Card className="border-amber-300 bg-amber-50 dark:border-amber-800/60 dark:bg-amber-950/30">
          <CardContent className="flex items-start gap-4 p-6 text-amber-950 dark:text-amber-100">
            <ShieldCheck className="mt-1 h-6 w-6 shrink-0" />
            <div className="space-y-2">
              <h2 className="text-lg font-semibold">هذه الوحدة متاحة للحسابات المؤسسية فقط</h2>
              <p className="text-sm leading-7">مركز ربط الأجهزة والـGateway مخصص لحسابات المؤسسات المرتبطة بمختبر أو منشأة. حسابات الأفراد والمواطنين لا يمكنها الوصول إلى هذه البيانات أو عمليات المراقبة.</p>
              <p className="text-xs text-amber-800 dark:text-amber-200">إذا كنت تعمل ضمن مؤسسة صحية، اطلب من مسؤول المؤسسة إنشاء أو ربط حساب LabUser مناسب.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const probe = async (device: DeviceIntegrationRecord) => {
    setActionUid(device.device_uid);
    setError("");
    try {
      if (demoMode) {
        setDevices((current) => current.map((item) => item.device_uid === device.device_uid ? { ...item, status: "connected", last_seen_at: new Date().toISOString() } : item));
        setSummary((current) => ({ ...current, connected: current.connected + (device.status === "connected" ? 0 : 1), disconnected: Math.max(0, current.disconnected - (device.status === "disconnected" ? 1 : 0)), error: Math.max(0, current.error - (device.status === "error" ? 1 : 0)), maintenance: Math.max(0, current.maintenance - (device.status === "maintenance" ? 1 : 0)) }));
      } else {
        const updated = await deviceIntegrationApi.probe(device.device_uid);
        setDevices((current) => current.map((item) => item.device_uid === updated.device_uid ? updated : item));
      }
    } catch {
      setError(`تعذر تنفيذ probe للمورد ${device.device_uid}.`);
    } finally {
      setActionUid(null);
    }
  };

  const createPrintJob = async () => {
    const printer = printerDevices[0];
    if (!printer) {
      setError("لا توجد طابعة مسجلة في الكتالوج.");
      return;
    }
    setActionUid(printer.device_uid);
    setError("");
    const payload = { device_uid: printer.device_uid, document_type: printer.protocol === "ZPL" || printer.protocol === "IPL" ? "specimen_label" : "report", printer_language: printer.protocol === "ZPL" || printer.protocol === "IPL" ? printer.protocol : "PDF", label_count: printer.protocol === "ZPL" || printer.protocol === "IPL" ? 1 : 1, template_key: "device-hub-demo" };
    try {
      if (demoMode) {
        const now = new Date().toISOString();
        setJobs((current) => [{ id: Date.now(), device_uid: printer.device_uid, document_type: payload.document_type as DeviceIntegrationPrinterJob["document_type"], printer_language: payload.printer_language as DeviceIntegrationPrinterJob["printer_language"], label_count: 1, status: "simulated_success", simulation_only: true, safe_metadata: { template_key: payload.template_key }, created_at: now, completed_at: now }, ...current]);
      } else {
        const job = await deviceIntegrationApi.createPrinterJob(payload);
        setJobs((current) => [job, ...current]);
      }
    } catch {
      setError("تعذر إنشاء وظيفة الطباعة المحاكية.");
    } finally {
      setActionUid(null);
    }
  };

  const simulate = async (connector: DeviceIntegrationConnectorRecord) => {
    const simulator = simulators.find((candidate) => candidate.protocol === connector.protocol);
    if (!simulator) {
      setError(`لا يوجد محاكي محلي معتمد للبروتوكول ${connector.protocol}.`);
      return;
    }
    setActionUid(connector.connector_uid);
    setError("");
    try {
      if (demoMode) {
        const now = new Date().toISOString();
        setConnectors((current) => current.map((item) => item.connector_uid === connector.connector_uid ? { ...item, status: "healthy", last_heartbeat_at: now, last_error: undefined, updated_at: now } : item));
        const deviceUid = connector.device_uid;
        if (deviceUid) {
          setDevices((current) => current.map((item) => item.device_uid === deviceUid ? { ...item, status: "connected", last_seen_at: now } : item));
          setEvents((current) => [{ id: Date.now(), device_uid: deviceUid, event_type: "simulated_protocol_exchange", direction: simulator.family === "printing" ? "outbound" : "inbound", severity: "info", message_type: simulator.key, summary: `اكتملت محاكاة ${simulator.label} دون payload خام`, correlation_id: `demo-${Date.now()}`, safe_metadata: { simulation_only: true, connector_uid: connector.connector_uid, raw_payload_stored: false }, occurred_at: now }, ...current]);
        }
      } else {
        const result = await deviceIntegrationApi.simulate(connector.connector_uid, { simulator_key: simulator.key, scenario: "success", item_count: 1 });
        setConnectors((current) => current.map((item) => item.connector_uid === connector.connector_uid ? { ...item, status: result.connector_status, last_heartbeat_at: new Date().toISOString(), last_error: undefined } : item));
        if (result.device_status && connector.device_uid) setDevices((current) => current.map((item) => item.device_uid === connector.device_uid ? { ...item, status: result.device_status as DeviceIntegrationStatus, last_seen_at: new Date().toISOString() } : item));
      }
    } catch {
      setError(`تعذر تشغيل المحاكي ${simulator.key}.`);
    } finally {
      setActionUid(null);
    }
  };

  const acknowledgeAlert = async (alert: DeviceGatewayAlertRecord) => {
    if (alert.status === "resolved") return;
    setAlertActionId(alert.id);
    setError("");
    try {
      const now = new Date().toISOString();
      const updated = demoMode
        ? { ...alert, status: "acknowledged" as const, acknowledged_at: now, acknowledged_by: 1 }
        : await deviceIntegrationApi.acknowledgeMonitoringAlert(alert.id, { note: "تمت المراجعة من مركز المراقبة" });
      setMonitoring((current) => ({ ...current, alerts: current.alerts.map((item) => item.id === alert.id ? updated : item) }));
    } catch {
      setError(`تعذر تأكيد التنبيه ${alert.title}.`);
    } finally {
      setAlertActionId(null);
    }
  };

  const tabs = [
    { key: "overview" as const, label: "النظرة العامة", icon: Activity },
    { key: "devices" as const, label: "كتالوج الأجهزة", icon: Server },
    { key: "connectors" as const, label: "الموصلات", icon: Link2 },
    { key: "protocols" as const, label: "البروتوكولات", icon: Cable },
    { key: "profiles" as const, label: "Profiles", icon: Tags },
    { key: "simulators" as const, label: "المحاكيات", icon: FlaskConical },
    { key: "events" as const, label: "سجل الأحداث", icon: FileOutput },
    { key: "printing" as const, label: "الطباعة", icon: Printer },
    { key: "monitoring" as const, label: "المراقبة والتنبيهات", icon: AlertTriangle },
    { key: "chronic_care" as const, label: "الرعاية المزمنة", icon: Stethoscope },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-6" dir="rtl">
      <PageHeader title="مركز ربط الأجهزة" description="كتالوج موحّد للأجهزة الطبية والمختبرية والتصوير والطابعات ومحطات العمل والشبكات، مع مراقبة اتصال محاكاة محلية." />

      <Card className="overflow-hidden border-slate-800 bg-gradient-to-l from-slate-950 via-slate-900 to-cyan-950 text-white shadow-xl">
        <CardContent className="p-6">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-3xl space-y-3">
              <div className="flex items-center gap-2 text-cyan-300"><ShieldCheck className="h-5 w-5" /><span className="text-sm font-semibold tracking-wide">DEVICE INTEGRATION HUB</span></div>
              <h2 className="text-2xl font-bold tracking-tight">طبقة واحدة لكل جهاز، وبوابة آمنة لكل بروتوكول</h2>
              <p className="text-sm leading-7 text-slate-300">تفصل هذه الوحدة بين تعريف الجهاز، طريقة النقل، بروتوكول الرسالة، وسجل الحالة. لا تُرسل بيانات إلى أجهزة حقيقية من هذه الشاشة، ولا تُحفظ payloads خام قد تحتوي على معلومات صحية.</p>
              <div className="flex flex-wrap gap-2"><Badge variant="success"><CheckCircle2 className="ml-1 h-3.5 w-3.5" />محاكاة محلية معزولة</Badge><Badge variant="outline" className="border-slate-600 text-slate-200"><Link2 className="ml-1 h-3.5 w-3.5" />Adapter gateway لاحقًا</Badge><Badge variant="outline" className="border-slate-600 text-slate-200"><ShieldCheck className="ml-1 h-3.5 w-3.5" />سجل أحداث آمن</Badge></div>
            </div>
            <div className="min-w-[255px] space-y-3 rounded-2xl border border-white/10 bg-white/[0.07] p-4 backdrop-blur">
              <div className="flex items-center justify-between text-sm"><span className="text-slate-300">وضع الاتصال</span><span className="font-semibold text-cyan-300">{demoMode ? "Demo / Synthetic" : "Live + guarded"}</span></div>
              <div className="flex items-center justify-between text-sm"><span className="text-slate-300">أجهزة الكتالوج</span><strong>{summary.total}</strong></div>
              <div className="flex items-center justify-between text-sm"><span className="text-slate-300">متصلة</span><strong className="text-emerald-300">{summary.connected}</strong></div>
              {!demoMode && <Button variant="outline" size="sm" className="w-full border-slate-600 bg-transparent text-white hover:bg-white/10" onClick={() => void loadLive()} disabled={loading}><RefreshCw className={`ml-1 h-4 w-4 ${loading ? "animate-spin" : ""}`} />تحديث الحالة</Button>}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm leading-7 text-amber-950 dark:border-amber-800/60 dark:bg-amber-950/30 dark:text-amber-100"><strong>حدود تشغيل إلزامية:</strong> كل السجلات والـprobes ووظائف الطباعة في هذه الدفعة محاكاة محلية فقط. قبل الاستخدام الإنتاجي يلزم Adapter خادمي/محلي معتمد، TLS أو mTLS، allowlist للشبكة، إدارة أسرار، واختبار بروتوكول خاص بكل طراز؛ لا يُسمح للـAPI العام بفتح USB أو Serial أو Bluetooth أو منافذ TCP مباشرة.</div>
      {loading && <div className="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900" role="status"><Loader2 className="ml-2 inline h-4 w-4 animate-spin" />جارٍ تحميل حالة الأجهزة من backend...</div>}
      {error && <div className="rounded-xl border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-950" role="alert"><AlertTriangle className="ml-2 inline h-4 w-4" />{error}</div>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        <MetricCard label="كل الأجهزة" value={summary.total} icon={Server} tone="slate" />
        <MetricCard label="متصل" value={summary.connected} icon={CheckCircle2} tone="emerald" />
        <MetricCard label="منفصل" value={summary.disconnected} icon={CircleOff} tone="amber" />
        <MetricCard label="أخطاء" value={summary.error} icon={XCircle} tone="rose" />
        <MetricCard label="صيانة" value={summary.maintenance} icon={Clock3} tone="violet" />
        <MetricCard label="أحداث 24 ساعة" value={summary.recent_events} icon={Activity} tone="cyan" />
      </div>

      <div className="flex flex-wrap gap-2 rounded-2xl border bg-card p-2 shadow-sm" role="tablist" aria-label="أقسام مركز ربط الأجهزة">
        {tabs.map(({ key, label, icon: Icon }) => <button key={key} type="button" role="tab" aria-selected={activeTab === key} onClick={() => setActiveTab(key)} className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${activeTab === key ? "bg-slate-900 text-white shadow-sm dark:bg-cyan-500/20 dark:text-cyan-100" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}><Icon className="h-4 w-4" />{label}</button>)}
      </div>

      {activeTab === "overview" && <OverviewTab devices={devices} summary={summary} events={events} protocols={protocols} onProbe={probe} actionUid={actionUid} onGo={(tab) => setActiveTab(tab)} />}
      {activeTab === "devices" && <DevicesTab devices={filteredDevices} search={search} setSearch={setSearch} selectedCategory={selectedCategory} setSelectedCategory={setSelectedCategory} onProbe={probe} actionUid={actionUid} />}
      {activeTab === "connectors" && <ConnectorsTab connectors={connectors} onSimulate={simulate} actionUid={actionUid} />}
      {activeTab === "protocols" && <ProtocolsTab protocols={protocols} />}
      {activeTab === "profiles" && <ProfilesTab profiles={profiles} />}
      {activeTab === "simulators" && <SimulatorsTab simulators={simulators} connectors={connectors} onSimulate={simulate} actionUid={actionUid} />}
      {activeTab === "events" && <EventsTab events={events} />}
      {activeTab === "printing" && <PrintingTab jobs={jobs} printers={printerDevices} onCreate={createPrintJob} actionUid={actionUid} />}
      {activeTab === "monitoring" && <MonitoringTab monitoring={monitoring} onAcknowledge={acknowledgeAlert} alertActionId={alertActionId} />}
      {activeTab === "chronic_care" && <ChronicCareTab summary={baselineSummary} patientId={baselinePatientId} metricCode={baselineMetric} loading={baselineLoading} setPatientId={setBaselinePatientId} setMetricCode={setBaselineMetric} onLoad={loadBaselineSummary} demoMode={demoMode} />}
    </div>
  );
}

function ChronicCareTab({
  summary,
  patientId,
  metricCode,
  loading,
  setPatientId,
  setMetricCode,
  onLoad,
  demoMode,
}: {
  summary: WearableBaselineSummary | null;
  patientId: string;
  metricCode: string;
  loading: boolean;
  setPatientId: (value: string) => void;
  setMetricCode: (value: string) => void;
  onLoad: () => Promise<void>;
  demoMode: boolean;
}) {
  const latestValue = summary?.latest.value ?? 0;
  const lower = summary?.baseline.lower_bound ?? latestValue;
  const upper = summary?.baseline.upper_bound ?? latestValue;
  const range = Math.max(upper - lower, 1);
  const markerPosition = Math.min(100, Math.max(0, ((latestValue - lower) / range) * 100));
  const anomaly = summary?.evaluation.is_anomaly ?? false;
  const metricLabel: Record<string, string> = {
    systolic_bp: "ضغط الدم الانقباضي",
    diastolic_bp: "ضغط الدم الانبساطي",
    heart_rate: "معدل النبض",
    spo2: "تشبع الأكسجين",
    blood_glucose: "سكر الدم",
    weight: "الوزن",
  };

  return <div className="space-y-6">
    <Card className="border-cyan-200 bg-cyan-50/60 dark:border-cyan-900/60 dark:bg-cyan-950/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base"><Stethoscope className="h-5 w-5 text-cyan-700" />محرك الرعاية المزمنة — baseline شخصي</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-7 text-muted-foreground">يعرض هذا القسم انحراف القراءة الأخيرة عن النمط التاريخي للمريض باستخدام إحصاءات مقاومة للشذوذ. المخرجات استشارية فقط، ولا تغيّر الدواء أو خطة الرعاية ولا تغلق التنبيه تلقائيًا.</p>
        <form className="grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end" onSubmit={(event) => { event.preventDefault(); void onLoad(); }}>
          <label className="space-y-1.5 text-sm font-medium"><span>رقم المريض</span><input type="number" min="1" value={patientId} onChange={(event) => setPatientId(event.target.value)} className="h-10 w-full rounded-lg border bg-background px-3" required /></label>
          <label className="space-y-1.5 text-sm font-medium"><span>المؤشر الحيوي</span><select value={metricCode} onChange={(event) => setMetricCode(event.target.value)} className="h-10 w-full rounded-lg border bg-background px-3"><option value="systolic_bp">ضغط انقباضي</option><option value="diastolic_bp">ضغط انبساطي</option><option value="heart_rate">نبض</option><option value="spo2">SpO₂</option><option value="blood_glucose">سكر الدم</option><option value="weight">الوزن</option></select></label>
          <Button type="submit" disabled={loading}>{loading ? <Loader2 className="ml-2 h-4 w-4 animate-spin" /> : <RefreshCw className="ml-2 h-4 w-4" />}تحميل الملخص</Button>
        </form>
        <div className="flex flex-wrap items-center gap-2 text-xs"><Badge variant="success"><ShieldCheck className="ml-1 h-3.5 w-3.5" />advisory_only=true</Badge>{demoMode && <Badge variant="outline">Demo / Synthetic</Badge>}<span className="text-muted-foreground">لا تُحفظ payloads الخام لمزود الجهاز.</span></div>
      </CardContent>
    </Card>

    {!summary ? <Card><CardContent className="p-8 text-center text-sm text-muted-foreground">أدخل رقم المريض والمؤشر ثم اضغط «تحميل الملخص» لعرض baseline الاستشاري.</CardContent></Card> : <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="آخر قراءة" value={`${summary.latest.value} ${summary.latest.unit}`} icon={Activity} tone={anomaly ? "rose" : "cyan"} />
        <MetricCard label="الوسيط الشخصي" value={summary.baseline.median ?? "—"} icon={Gauge} tone="violet" />
        <MetricCard label="عدد القراءات" value={summary.measurement_count} icon={Activity} tone="slate" />
        <MetricCard label="الثقة الإحصائية" value={`${Math.round(summary.baseline.confidence * 100)}%`} icon={ShieldCheck} tone="emerald" />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader><CardTitle className="text-base">النطاق الشخصي المتعلم — {metricLabel[summary.metric_code] ?? summary.metric_code}</CardTitle></CardHeader>
          <CardContent className="space-y-5">
            <div className="relative pt-6"><div className="h-4 rounded-full bg-gradient-to-l from-rose-300 via-emerald-300 to-rose-300 dark:from-rose-900 dark:via-emerald-900 dark:to-rose-900" /><div className="absolute top-0 -translate-x-1/2 text-xs font-semibold" style={{ left: `${markerPosition}%` }}>{summary.latest.value}</div><div className="absolute top-5 h-3 w-0.5 bg-slate-900 dark:bg-white" style={{ left: `${markerPosition}%` }} /></div>
            <div className="flex justify-between text-xs text-muted-foreground"><span>الحد الأدنى {summary.baseline.lower_bound ?? "—"}</span><span>الحد الأعلى {summary.baseline.upper_bound ?? "—"}</span></div>
            <div className={`rounded-xl border p-4 ${anomaly ? "border-amber-300 bg-amber-50 text-amber-950 dark:border-amber-800/60 dark:bg-amber-950/30 dark:text-amber-100" : "border-emerald-200 bg-emerald-50 text-emerald-950 dark:border-emerald-900/60 dark:bg-emerald-950/20 dark:text-emerald-100"}`}><div className="flex items-start gap-3"><AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" /><p className="text-sm leading-7">{summary.evaluation.explanation}</p></div></div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-base">حالة التقييم</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm"><div className="flex items-center justify-between rounded-xl bg-muted/50 px-3 py-2.5"><span>الحالة</span><Badge variant={anomaly ? "warning" : "success"}>{anomaly ? "يحتاج مراجعة" : "ضمن النمط الشخصي"}</Badge></div><div className="flex items-center justify-between rounded-xl bg-muted/50 px-3 py-2.5"><span>درجة الانحراف</span><strong>{summary.evaluation.deviation_score ?? "—"}</strong></div><div className="flex items-center justify-between rounded-xl bg-muted/50 px-3 py-2.5"><span>مصدر آخر قراءة</span><strong>{summary.latest.source}</strong></div><div className="flex items-center justify-between rounded-xl bg-muted/50 px-3 py-2.5"><span>آخر تحديث baseline</span><strong>{formatTime(summary.baseline.generated_at)}</strong></div><p className="pt-2 text-xs leading-6 text-muted-foreground">يجب على الطبيب مراجعة الاتجاه والسياق والأعراض والسجل الطبي قبل اتخاذ أي قرار. لا يمثل هذا التقييم تشخيصًا أو توصية علاجية.</p></CardContent>
        </Card>
      </div>
    </>}
  </div>;
}

function OverviewTab({ devices, summary, events, protocols, onProbe, actionUid, onGo }: { devices: DeviceIntegrationRecord[]; summary: DeviceIntegrationSummary; events: DeviceIntegrationEventRecord[]; protocols: DeviceIntegrationProtocolDescriptor[]; onProbe: (device: DeviceIntegrationRecord) => void; actionUid: string | null; onGo: (tab: "devices" | "protocols" | "events" | "printing") => void }) {
  return <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
    <Card>
      <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Activity className="h-5 w-5 text-cyan-600" />خريطة الحالة الحالية</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {devices.slice(0, 6).map((device) => <DeviceRow key={device.device_uid} device={device} onProbe={onProbe} actionUid={actionUid} />)}
        <button type="button" onClick={() => onGo("devices")} className="w-full rounded-xl border border-dashed p-3 text-sm font-semibold text-cyan-700 transition hover:bg-cyan-50 dark:text-cyan-300 dark:hover:bg-cyan-950/20">عرض كل الأجهزة في الكتالوج</button>
      </CardContent>
    </Card>
    <div className="space-y-6">
      <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Router className="h-5 w-5 text-indigo-600" />توزيع الفئات</CardTitle></CardHeader><CardContent className="space-y-3">{Object.entries(summary.by_category).map(([category, count]) => <div key={category} className="flex items-center justify-between rounded-xl bg-muted/50 px-3 py-2.5"><span className="text-sm">{CATEGORY_LABELS[category as DeviceIntegrationCategory] ?? category}</span><span className="font-bold">{count}</span></div>)}<div className="flex items-center justify-between rounded-xl border border-cyan-200 bg-cyan-50 px-3 py-2.5 text-sm text-cyan-950 dark:border-cyan-900/50 dark:bg-cyan-950/20 dark:text-cyan-100"><span>بروتوكولات مفهرسة</span><strong>{protocols.length}</strong></div></CardContent></Card>
      <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><FileOutput className="h-5 w-5 text-amber-600" />آخر الأحداث</CardTitle></CardHeader><CardContent className="space-y-3">{events.slice(0, 3).map((event) => <div key={event.id} className="rounded-xl border p-3"><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold">{event.summary}</p><p className="mt-1 text-xs text-muted-foreground">{event.device_uid} · {formatTime(event.occurred_at)}</p></div><SeverityBadge severity={event.severity} /></div></div>)}<button type="button" onClick={() => onGo("events")} className="w-full rounded-xl border border-dashed p-3 text-sm font-semibold text-amber-700 transition hover:bg-amber-50 dark:text-amber-300 dark:hover:bg-amber-950/20">فتح سجل الأحداث الكامل</button></CardContent></Card>
    </div>
  </div>;
}

function DevicesTab({ devices, search, setSearch, selectedCategory, setSelectedCategory, onProbe, actionUid }: { devices: DeviceIntegrationRecord[]; search: string; setSearch: (value: string) => void; selectedCategory: "all" | DeviceIntegrationCategory; setSelectedCategory: (value: "all" | DeviceIntegrationCategory) => void; onProbe: (device: DeviceIntegrationRecord) => void; actionUid: string | null }) {
  return <Card><CardHeader><div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"><CardTitle className="flex items-center gap-2 text-base"><Server className="h-5 w-5 text-cyan-600" />كتالوج الأجهزة ({devices.length})</CardTitle><div className="flex flex-col gap-2 sm:flex-row"><label className="relative"><Search className="pointer-events-none absolute right-3 top-2.5 h-4 w-4 text-muted-foreground" /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="بحث بالاسم أو UID أو البروتوكول" className="h-9 w-full rounded-lg border bg-background pr-9 pl-3 text-sm outline-none ring-offset-background focus:ring-2 focus:ring-cyan-500 sm:w-72" /></label><select value={selectedCategory} onChange={(event) => setSelectedCategory(event.target.value as "all" | DeviceIntegrationCategory)} className="h-9 rounded-lg border bg-background px-3 text-sm"><option value="all">كل الفئات</option>{Object.entries(CATEGORY_LABELS).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></div></div></CardHeader><CardContent><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{devices.map((device) => <DeviceCard key={device.device_uid} device={device} onProbe={onProbe} actionUid={actionUid} />)}</div>{!devices.length && <div className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">لا توجد أجهزة تطابق البحث الحالي.</div>}</CardContent></Card>;
}

function ProtocolsTab({ protocols }: { protocols: DeviceIntegrationProtocolDescriptor[] }) {
  return <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Cable className="h-5 w-5 text-indigo-600" />كتالوج البروتوكولات وطبقات النقل</CardTitle></CardHeader><CardContent><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{protocols.map((protocol) => <div key={protocol.key} className="rounded-2xl border bg-gradient-to-br from-card to-muted/40 p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold">{protocol.label}</p><p className="mt-1 text-xs text-muted-foreground">{protocol.family}</p></div><Badge variant="success">محاكاة</Badge></div><div className="mt-4 flex flex-wrap gap-1.5">{protocol.transports.map((transport) => <span key={transport} className="rounded-full bg-slate-900 px-2 py-1 text-[11px] text-white dark:bg-white/10">{transport}</span>)}</div><p className="mt-4 text-sm leading-6 text-muted-foreground">{protocol.production_requirement}</p><div className="mt-4 flex flex-wrap gap-1.5">{protocol.intended_categories.map((category) => <span key={category} className="rounded-full border px-2 py-1 text-[11px]">{CATEGORY_LABELS[category]}</span>)}</div></div>)}</div></CardContent></Card>;
}

function ConnectorsTab({ connectors, onSimulate, actionUid }: { connectors: DeviceIntegrationConnectorRecord[]; onSimulate: (connector: DeviceIntegrationConnectorRecord) => void; actionUid: string | null }) {
  return <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Link2 className="h-5 w-5 text-cyan-600" />سجل الموصلات والـGateway</CardTitle></CardHeader><CardContent><div className="grid gap-4 md:grid-cols-2">{connectors.map((connector) => <div key={connector.connector_uid} className="rounded-2xl border bg-gradient-to-br from-card to-muted/40 p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold">{connector.display_name}</p><p className="mt-1 font-mono text-[11px] text-muted-foreground">{connector.connector_uid}</p></div><ConnectorStatusBadge status={connector.status} /></div><div className="mt-4 grid grid-cols-2 gap-2 text-xs"><span className="rounded-lg bg-muted px-2 py-1.5">{connector.protocol}</span><span className="rounded-lg bg-muted px-2 py-1.5">{connector.transport}</span><span className="rounded-lg bg-muted px-2 py-1.5">{connector.mode === "gateway_pending" ? "Gateway pending" : "محاكاة"}</span><span className="rounded-lg bg-muted px-2 py-1.5">{connector.contract_version}</span></div><p className="mt-3 text-xs text-muted-foreground">{connector.device_uid ?? "غير مرتبط بجهاز"} · آخر heartbeat: {formatTime(connector.last_heartbeat_at)}</p>{connector.last_error && <p className="mt-2 rounded-lg bg-rose-50 px-2 py-1.5 text-xs text-rose-800 dark:bg-rose-950/30 dark:text-rose-200">{connector.last_error}</p>}<Button variant="outline" size="sm" className="mt-4 w-full" onClick={() => onSimulate(connector)} disabled={actionUid !== null || !connector.simulation_only}>{actionUid === connector.connector_uid ? <Loader2 className="h-4 w-4 animate-spin" /> : "تشغيل exchange محاكى"}</Button></div>)}</div>{!connectors.length && <p className="text-sm text-muted-foreground">لا توجد موصلات مسجلة.</p>}<p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs leading-6 text-amber-950 dark:border-amber-800/50 dark:bg-amber-950/20 dark:text-amber-100">الموصلات النشطة غير مسموحة من API العام؛ `gateway_pending` يعني أن Gateway مؤسسيًا مطلوب قبل الاتصال الفعلي.</p></CardContent></Card>;
}

function ProfilesTab({ profiles }: { profiles: DeviceIntegrationProtocolProfileRecord[] }) {
  return <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Tags className="h-5 w-5 text-indigo-600" />قوالب البروتوكولات وMapping Contracts</CardTitle></CardHeader><CardContent><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{profiles.map((profile) => <div key={profile.profile_key} className="rounded-2xl border p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold">{profile.profile_key}</p><p className="mt-1 text-xs text-muted-foreground">{profile.protocol} · {profile.version}</p></div><Badge variant={profile.status === "validated" ? "success" : profile.status === "retired" ? "outline" : "warning"}>{profile.status === "validated" ? "متحقق" : profile.status === "retired" ? "متقاعد" : "مسودة"}</Badge></div><div className="mt-4 space-y-2 text-xs text-muted-foreground"><p>message: {profile.message_type ?? "غير محدد"}</p><p>framing: {profile.framing ?? "غير محدد"} · ACK: {profile.ack_strategy ?? "غير محدد"}</p><p>simulator: {profile.simulator_key ?? "غير محدد"}</p></div><div className="mt-4 flex flex-wrap gap-1.5"><span className="rounded-full border px-2 py-1 text-[11px]">mapping محفوظ</span><span className="rounded-full border px-2 py-1 text-[11px]">simulation_only</span></div></div>)}</div>{!profiles.length && <p className="text-sm text-muted-foreground">لا توجد profiles.</p>}</CardContent></Card>;
}

function SimulatorsTab({ simulators, connectors, onSimulate, actionUid }: { simulators: DeviceIntegrationSimulatorDescriptor[]; connectors: DeviceIntegrationConnectorRecord[]; onSimulate: (connector: DeviceIntegrationConnectorRecord) => void; actionUid: string | null }) {
  return <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><FlaskConical className="h-5 w-5 text-violet-600" />مختبر المحاكيات الآمن</CardTitle></CardHeader><CardContent><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{simulators.map((simulator) => { const connector = connectors.find((candidate) => candidate.protocol === simulator.protocol); return <div key={simulator.key} className="rounded-2xl border bg-card p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold">{simulator.label}</p><p className="mt-1 text-xs text-muted-foreground">{simulator.protocol} · {simulator.family}</p></div><Badge variant="success">محلي</Badge></div><p className="mt-4 text-sm leading-6 text-muted-foreground">{simulator.contract_summary}</p><p className="mt-2 text-xs text-muted-foreground">المخرج: {simulator.output}</p><Button variant="outline" size="sm" className="mt-4 w-full" onClick={() => connector && onSimulate(connector)} disabled={!connector || actionUid !== null}>{connector ? "اختبار على Connector" : "لا يوجد Connector"}</Button></div>; })}</div><p className="mt-4 rounded-xl border border-cyan-200 bg-cyan-50 p-3 text-xs leading-6 text-cyan-950 dark:border-cyan-900/50 dark:bg-cyan-950/20 dark:text-cyan-100">لا يتم بناء HL7/ASTM/DICOM payload خام داخل المتصفح ولا تخزينه؛ المحاكي يسجل contract summary وcorrelation فقط.</p></CardContent></Card>;
}

function EventsTab({ events }: { events: DeviceIntegrationEventRecord[] }) {
  return <Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><FileOutput className="h-5 w-5 text-amber-600" />سجل الأحداث الآمن</CardTitle></CardHeader><CardContent className="space-y-3">{events.map((event) => <div key={event.id} className="rounded-2xl border p-4"><div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between"><div><div className="flex flex-wrap items-center gap-2"><p className="font-semibold">{event.summary}</p><SeverityBadge severity={event.severity} /></div><p className="mt-1 text-xs text-muted-foreground">{event.device_uid} · {event.event_type} · {event.direction} · {formatTime(event.occurred_at)}</p></div><span className="rounded-lg bg-muted px-2 py-1 font-mono text-[11px] text-muted-foreground">{event.correlation_id}</span></div><div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">{Object.entries(event.safe_metadata ?? {}).map(([key, value]) => <span key={key} className="rounded-full border px-2 py-1">{key}: {String(value)}</span>)}</div></div>)}{!events.length && <p className="text-sm text-muted-foreground">لا توجد أحداث مسجلة لهذا المختبر.</p>}</CardContent></Card>;
}

function PrintingTab({ jobs, printers, onCreate, actionUid }: { jobs: DeviceIntegrationPrinterJob[]; printers: DeviceIntegrationRecord[]; onCreate: () => void; actionUid: string | null }) {
  return <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]"><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Printer className="h-5 w-5 text-violet-600" />إدارة الطابعات</CardTitle></CardHeader><CardContent className="space-y-3">{printers.map((printer) => <div key={printer.device_uid} className="rounded-2xl border p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold">{printer.display_name}</p><p className="mt-1 text-xs text-muted-foreground">{printer.device_uid} · {printer.protocol} · {printer.transport}</p></div><StatusBadge status={printer.status} /></div><p className="mt-3 text-xs text-muted-foreground">{printer.printer_profile ? Object.entries(printer.printer_profile).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`).join(" · ") : "لا يوجد ملف طابعة"}</p></div>)}<Button className="w-full" onClick={onCreate} disabled={!printers.length || actionUid !== null}><Printer className="ml-2 h-4 w-4" />إنشاء وظيفة طباعة محاكاة</Button><p className="text-xs leading-6 text-muted-foreground">تُحفظ الوظيفة كـsimulation_only ولا تُرسل ZPL/IPL/PDF إلى طابعة حقيقية.</p></CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2 text-base"><FileOutput className="h-5 w-5 text-indigo-600" />آخر وظائف الطباعة</CardTitle></CardHeader><CardContent className="space-y-3">{jobs.map((job) => <div key={job.id} className="rounded-2xl border p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold">{job.document_type} · {job.printer_language}</p><p className="mt-1 text-xs text-muted-foreground">{job.device_uid} · {job.label_count} عنصر · {formatTime(job.created_at)}</p></div><Badge variant={job.status === "simulated_success" ? "success" : job.status === "failed" ? "destructive" : "warning"}>{job.status === "simulated_success" ? "محاكاة ناجحة" : job.status === "failed" ? "فشل" : "بالانتظار"}</Badge></div></div>)}{!jobs.length && <p className="text-sm text-muted-foreground">لا توجد وظائف طباعة.</p>}</CardContent></Card></div>;
}

function DeviceRow({ device, onProbe, actionUid }: { device: DeviceIntegrationRecord; onProbe: (device: DeviceIntegrationRecord) => void; actionUid: string | null }) {
  const Icon = deviceIcon(device.category);
  return <div className="flex flex-col gap-3 rounded-2xl border p-4 sm:flex-row sm:items-center sm:justify-between"><div className="flex min-w-0 items-center gap-3"><span className="rounded-xl bg-cyan-500/10 p-2.5 text-cyan-700 dark:text-cyan-300"><Icon className="h-5 w-5" /></span><div className="min-w-0"><p className="truncate text-sm font-semibold">{device.display_name}</p><p className="mt-1 truncate text-xs text-muted-foreground">{device.device_uid} · {device.protocol} · {device.transport}</p></div></div><div className="flex items-center gap-2"><StatusBadge status={device.status} /><Button variant="outline" size="sm" onClick={() => onProbe(device)} disabled={actionUid !== null}>{actionUid === device.device_uid ? <Loader2 className="h-4 w-4 animate-spin" /> : "Probe"}</Button></div></div>;
}

function DeviceCard({ device, onProbe, actionUid }: { device: DeviceIntegrationRecord; onProbe: (device: DeviceIntegrationRecord) => void; actionUid: string | null }) {
  const Icon = deviceIcon(device.category);
  return <div className="group rounded-2xl border bg-card p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"><div className="flex items-start justify-between gap-3"><span className="rounded-xl bg-slate-900 p-2.5 text-cyan-200 dark:bg-cyan-500/10 dark:text-cyan-300"><Icon className="h-5 w-5" /></span><StatusBadge status={device.status} /></div><div className="mt-4"><p className="font-semibold leading-6">{device.display_name}</p><p className="mt-1 font-mono text-[11px] text-muted-foreground">{device.device_uid}</p></div><div className="mt-4 grid grid-cols-2 gap-2 text-xs"><span className="rounded-lg bg-muted px-2 py-1.5">{CATEGORY_LABELS[device.category]}</span><span className="rounded-lg bg-muted px-2 py-1.5">{device.protocol}</span><span className="rounded-lg bg-muted px-2 py-1.5">{device.transport}</span><span className="rounded-lg bg-muted px-2 py-1.5">{device.simulation_only ? "محاكاة" : "فعلي"}</span></div><div className="mt-4 flex items-center justify-between gap-2"><span className="text-[11px] text-muted-foreground">آخر اتصال: {formatTime(device.last_seen_at)}</span><Button variant="outline" size="sm" onClick={() => onProbe(device)} disabled={actionUid !== null}>{actionUid === device.device_uid ? <Loader2 className="h-4 w-4 animate-spin" /> : "اختبار"}</Button></div></div>;
}

function ConnectorStatusBadge({ status }: { status: DeviceIntegrationConnectorRecord["status"] }) {
  const meta = CONNECTOR_STATUS_META[status];
  return <Badge variant={meta.variant}>{meta.label}</Badge>;
}

function StatusBadge({ status }: { status: DeviceIntegrationStatus }) {
  const meta = STATUS_META[status];
  const Icon = meta.icon;
  return <Badge variant={meta.variant}><Icon className={`ml-1 h-3.5 w-3.5 ${status === "pending" ? "animate-spin" : ""}`} />{meta.label}</Badge>;
}

function SeverityBadge({ severity }: { severity: DeviceIntegrationEventRecord["severity"] }) {
  return <Badge variant={severity === "error" ? "destructive" : severity === "warning" ? "warning" : "outline"}>{severity === "error" ? "خطأ" : severity === "warning" ? "تحذير" : "معلومة"}</Badge>;
}

function MetricCard({ label, value, icon: Icon, tone }: { label: string; value: number | string; icon: typeof Activity; tone: "slate" | "emerald" | "amber" | "rose" | "violet" | "cyan" }) {
  const tones = { slate: "bg-slate-500/10 text-slate-700 dark:text-slate-300", emerald: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300", amber: "bg-amber-500/10 text-amber-700 dark:text-amber-300", rose: "bg-rose-500/10 text-rose-700 dark:text-rose-300", violet: "bg-violet-500/10 text-violet-700 dark:text-violet-300", cyan: "bg-cyan-500/10 text-cyan-700 dark:text-cyan-300" };
  return <Card><CardContent className="flex items-center gap-3 p-4"><span className={`rounded-xl p-2.5 ${tones[tone]}`}><Icon className="h-5 w-5" /></span><div><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-xl font-bold">{value}</p></div></CardContent></Card>;
}


function MonitoringTab({ monitoring, onAcknowledge, alertActionId }: { monitoring: DeviceGatewayMonitoringSnapshot; onAcknowledge: (alert: DeviceGatewayAlertRecord) => void; alertActionId: number | null }) {
  const metric = monitoring.latest_metric;
  const diskTone = (metric?.disk_used_percent ?? 0) >= (monitoring.thresholds.disk_used_critical_percent ?? 95) ? "rose" : (metric?.disk_used_percent ?? 0) >= (monitoring.thresholds.disk_used_warning_percent ?? 85) ? "amber" : "emerald";
  const queueTone = (metric?.outbox_oldest_age_seconds ?? 0) >= (monitoring.thresholds.outbox_oldest_age_critical_seconds ?? 900) ? "rose" : (metric?.outbox_oldest_age_seconds ?? 0) >= (monitoring.thresholds.outbox_oldest_age_warning_seconds ?? 300) ? "amber" : "cyan";

  return <div className="space-y-6">
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
      <MetricCard label="Gateway سليمة" value={monitoring.healthy_gateway_count} icon={CheckCircle2} tone="emerald" />
      <MetricCard label="Gateway متدهورة" value={monitoring.degraded_gateway_count} icon={AlertTriangle} tone="amber" />
      <MetricCard label="غير متاحة" value={monitoring.offline_gateway_count} icon={CircleOff} tone="slate" />
      <MetricCard label="أقدم Outbox (ثانية)" value={Math.round(metric?.outbox_oldest_age_seconds ?? 0)} icon={Clock3} tone={queueTone} />
      <MetricCard label="استهلاك القرص %" value={Number((metric?.disk_used_percent ?? 0).toFixed(1))} icon={Gauge} tone={diskTone} />
      <MetricCard label="تنبيهات مفتوحة" value={monitoring.open_alert_count} icon={AlertTriangle} tone={monitoring.critical_alert_count > 0 ? "rose" : "cyan"} />
    </div>

    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Clock3 className="h-5 w-5 text-cyan-600" />حالة Outbox الدائمة</CardTitle></CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2">
          <MonitoringValue label="Pending" value={String(monitoring.outbox?.pending_count ?? metric?.outbox_pending_count ?? 0)} />
          <MonitoringValue label="Processing" value={String(monitoring.outbox?.processing_count ?? 0)} />
          <MonitoringValue label="Retry" value={String(monitoring.outbox?.retry_count ?? metric?.outbox_retry_count ?? 0)} />
          <MonitoringValue label="Dead Letter" value={String(monitoring.outbox?.dead_letter_count ?? metric?.outbox_dead_letter_count ?? 0)} />
          <MonitoringValue label="Delivered" value={String(monitoring.outbox?.delivered_count ?? 0)} />
          <MonitoringValue label="أقدم رسالة" value={`${Math.round(monitoring.outbox?.oldest_age_seconds ?? metric?.outbox_oldest_age_seconds ?? 0)} ثانية`} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Router className="h-5 w-5 text-indigo-600" />سجل Gateway المؤسسية</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {(monitoring.gateways ?? []).map((gateway) => <div key={gateway.gateway_ref} className="flex flex-col gap-2 rounded-xl border p-3 sm:flex-row sm:items-center sm:justify-between">
            <div><p className="font-semibold">{gateway.display_name}</p><p className="mt-1 font-mono text-[11px] text-muted-foreground">{gateway.gateway_ref} · {gateway.mode} · {gateway.contract_version}</p></div>
            <div className="text-right"><Badge variant={gateway.status === "healthy" ? "success" : gateway.status === "degraded" ? "warning" : gateway.status === "revoked" ? "destructive" : "outline"}>{gateway.status}</Badge><p className="mt-1 text-xs text-muted-foreground">Heartbeat: {formatTime(gateway.last_heartbeat_at)}</p></div>
          </div>)}
          {!(monitoring.gateways ?? []).length && <p className="text-sm text-muted-foreground">لا يوجد Gateway مسجل لهذا المختبر بعد.</p>}
        </CardContent>
      </Card>
    </div>

    <Card className="overflow-hidden border-slate-800 bg-gradient-to-l from-slate-950 via-slate-900 to-indigo-950 text-white">
      <CardContent className="p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2 text-indigo-300"><Activity className="h-5 w-5" /><span className="text-sm font-semibold tracking-wide">GATEWAY OBSERVABILITY</span></div>
            <h3 className="mt-2 text-xl font-bold">مراقبة الطابور والقرص وصحة العامل</h3>
            <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-300">تُقاس مؤشرات Outbox محليًا ثم تُرسل كـmetadata تشغيلية فقط. لا تعرض هذه اللوحة payloads خامًا أو أسماء مرضى، ولا تعني أن Gateway فعلية متصلة في هذه الدفعة.</p>
          </div>
          <Badge variant="outline" className="w-fit border-indigo-400/40 text-indigo-100"><ShieldCheck className="ml-1 h-4 w-4" />محاكاة آمنة فقط</Badge>
        </div>
      </CardContent>
    </Card>

    <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Server className="h-5 w-5 text-indigo-600" />آخر لقطة Gateway</CardTitle></CardHeader>
        <CardContent>
          {metric ? <div className="grid gap-3 sm:grid-cols-2">
            <MonitoringValue label="المعرف" value={metric.gateway_ref} />
            <MonitoringValue label="الحالة" value={metric.gateway_status === "healthy" ? "سليمة" : metric.gateway_status === "degraded" ? "متدهورة" : metric.gateway_status} />
            <MonitoringValue label="Pending Outbox" value={String(metric.outbox_pending_count)} />
            <MonitoringValue label="Retry" value={String(metric.outbox_retry_count)} />
            <MonitoringValue label="Dead Letter" value={String(metric.outbox_dead_letter_count)} />
            <MonitoringValue label="تأخر العامل" value={`${Math.round(metric.worker_lag_seconds)} ثانية`} />
            <MonitoringValue label="زمن النقل" value={metric.transport_latency_ms == null ? "غير متاح" : `${Math.round(metric.transport_latency_ms)} ms`} />
            <MonitoringValue label="آخر التقاط" value={formatTime(metric.captured_at)} />
          </div> : <p className="text-sm text-muted-foreground">لم تصل لقطة metrics بعد.</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Gauge className="h-5 w-5 text-amber-600" />عتبات التنبيه</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <ThresholdRow label="Outbox warning" value={`${monitoring.thresholds.outbox_oldest_age_warning_seconds ?? 300} ثانية`} />
          <ThresholdRow label="Outbox critical" value={`${monitoring.thresholds.outbox_oldest_age_critical_seconds ?? 900} ثانية`} />
          <ThresholdRow label="Disk warning" value={`${monitoring.thresholds.disk_used_warning_percent ?? 85}%`} />
          <ThresholdRow label="Disk critical" value={`${monitoring.thresholds.disk_used_critical_percent ?? 95}%`} />
          <ThresholdRow label="Worker lag warning" value={`${monitoring.thresholds.worker_lag_warning_seconds ?? 120} ثانية`} />
        </CardContent>
      </Card>
    </div>

    <Card>
      <CardHeader><div className="flex items-center justify-between gap-3"><CardTitle className="flex items-center gap-2 text-base"><AlertTriangle className="h-5 w-5 text-rose-600" />التنبيهات النشطة</CardTitle><Badge variant={monitoring.critical_alert_count > 0 ? "destructive" : "outline"}>{monitoring.critical_alert_count} حرج</Badge></div></CardHeader>
      <CardContent className="space-y-3">
        {monitoring.alerts.length === 0 && <p className="text-sm text-muted-foreground">لا توجد تنبيهات نشطة.</p>}
        {monitoring.alerts.map((alert) => <div key={alert.id} className="flex flex-col gap-3 rounded-2xl border p-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><AlertSeverityBadge severity={alert.severity} /><Badge variant={alert.status === "acknowledged" ? "success" : "outline"}>{alert.status === "acknowledged" ? "تمت المراجعة" : "مفتوح"}</Badge><span className="text-xs text-muted-foreground">{alert.gateway_ref}</span></div><p className="mt-2 font-semibold">{alert.title}</p><p className="mt-1 text-sm leading-6 text-muted-foreground">{alert.summary}</p><p className="mt-1 text-xs text-muted-foreground">القيمة: {alert.current_value == null ? "حالة" : alert.current_value} · الحد: {alert.threshold_value == null ? "—" : alert.threshold_value} · {formatTime(alert.last_seen_at)}</p></div>
          <Button variant="outline" size="sm" onClick={() => onAcknowledge(alert)} disabled={alert.status === "acknowledged" || alertActionId === alert.id}>{alertActionId === alert.id ? <Loader2 className="ml-1 h-4 w-4 animate-spin" /> : <CheckCircle2 className="ml-1 h-4 w-4" />}{alert.status === "acknowledged" ? "تمت المراجعة" : "تأكيد التنبيه"}</Button>
        </div>)}
      </CardContent>
    </Card>

    <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm leading-7 text-amber-950 dark:border-amber-800/60 dark:bg-amber-950/30 dark:text-amber-100"><strong>حدود التشغيل:</strong> هذه اللقطة اصطناعية في وضع Demo. الاتصال الفعلي يحتاج Gateway محلية موثقة بـmTLS، queue worker، heartbeat، وتدوير شهادات؛ لا تُعتبر التنبيهات بديلاً عن runbook أو مراقبة بنية المنشأة.</div>
  </div>;
}

function MonitoringValue({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl bg-muted/50 px-3 py-3"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-sm font-semibold break-words">{value}</p></div>;
}

function ThresholdRow({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between rounded-xl border px-3 py-2.5 text-sm"><span className="text-muted-foreground">{label}</span><strong>{value}</strong></div>;
}

function AlertSeverityBadge({ severity }: { severity: DeviceGatewayAlertRecord["severity"] }) {
  return <Badge variant={severity === "critical" ? "destructive" : severity === "warning" ? "warning" : "outline"}>{severity === "critical" ? "حرج" : severity === "warning" ? "تحذير" : "معلومة"}</Badge>;
}
