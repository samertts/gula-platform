import { index, int, json, mysqlEnum, mysqlTable, timestamp, uniqueIndex, varchar, text } from "drizzle-orm/mysql-core";

export const lisRoleValues = ["patient", "lab_staff", "physician", "institution_admin", "system_admin"] as const;
export const accountStatusValues = ["active", "suspended", "pending"] as const;
export const orderStatusValues = ["draft", "submitted", "sample_pending", "in_progress", "result_pending_review", "completed", "cancelled"] as const;
export const sampleStatusValues = ["expected", "received", "verified", "processing", "rejected", "completed"] as const;
export const resultStatusValues = ["not_started", "entered", "pending_review", "approved", "released", "rejected"] as const;
export const alertSeverityValues = ["critical", "high", "medium", "low"] as const;
export const notificationStatusValues = ["unread", "read", "archived"] as const;
export const taskStatusValues = ["pending", "in_progress", "completed", "cancelled"] as const;
export const taskPriorityValues = ["routine", "urgent", "critical"] as const;
export const approvalStatusValues = ["pending", "approved", "rejected", "cancelled"] as const;

export const institutions = mysqlTable("institutions", {
  id: int("id").autoincrement().primaryKey(),
  code: varchar("code", { length: 32 }).notNull(),
  nameAr: varchar("name_ar", { length: 255 }).notNull(),
  nameEn: varchar("name_en", { length: 255 }).notNull(),
  isActive: int("is_active").notNull().default(1),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [uniqueIndex("institutions_code_unique").on(table.code)]);

export const laboratories = mysqlTable("laboratories", {
  id: int("id").autoincrement().primaryKey(),
  institutionId: int("institution_id").notNull().references(() => institutions.id, { onDelete: "restrict" }),
  code: varchar("code", { length: 32 }).notNull(),
  nameAr: varchar("name_ar", { length: 255 }).notNull(),
  nameEn: varchar("name_en", { length: 255 }).notNull(),
  address: text("address"),
  isActive: int("is_active").notNull().default(1),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  uniqueIndex("laboratories_institution_code_unique").on(table.institutionId, table.code),
  index("laboratories_institution_idx").on(table.institutionId),
]);

export const users = mysqlTable("users", {
  id: int("id").autoincrement().primaryKey(),
  openId: varchar("open_id", { length: 64 }).notNull(),
  institutionId: int("institution_id").references(() => institutions.id, { onDelete: "restrict" }),
  laboratoryId: int("laboratory_id").references(() => laboratories.id, { onDelete: "restrict" }),
  name: varchar("name", { length: 255 }),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("login_method", { length: 64 }),
  role: mysqlEnum("role", lisRoleValues).notNull().default("patient"),
  accountStatus: mysqlEnum("account_status", accountStatusValues).notNull().default("pending"),
  staffIdentifier: varchar("staff_identifier", { length: 80 }),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("last_signed_in").defaultNow().notNull(),
}, (table) => [
  uniqueIndex("users_open_id_unique").on(table.openId),
  uniqueIndex("users_institution_email_unique").on(table.institutionId, table.email),
  index("users_institution_idx").on(table.institutionId),
  index("users_laboratory_idx").on(table.laboratoryId),
]);

export const userRoleAssignments = mysqlTable("user_role_assignments", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("user_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  institutionId: int("institution_id").notNull().references(() => institutions.id, { onDelete: "restrict" }),
  laboratoryId: int("laboratory_id").references(() => laboratories.id, { onDelete: "restrict" }),
  role: mysqlEnum("role", lisRoleValues).notNull(),
  isActive: int("is_active").notNull().default(1),
  assignedByUserId: int("assigned_by_user_id").references(() => users.id, { onDelete: "restrict" }),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  uniqueIndex("role_assignment_scope_unique").on(table.userId, table.institutionId, table.laboratoryId, table.role),
  index("role_assignment_user_idx").on(table.userId),
]);

export const patients = mysqlTable("patients", {
  id: int("id").autoincrement().primaryKey(),
  institutionId: int("institution_id").notNull().references(() => institutions.id, { onDelete: "restrict" }),
  linkedUserId: int("linked_user_id").references(() => users.id, { onDelete: "restrict" }),
  medicalRecordNumber: varchar("medical_record_number", { length: 64 }).notNull(),
  nationalId: varchar("national_id", { length: 64 }),
  firstName: varchar("first_name", { length: 120 }).notNull(),
  lastName: varchar("last_name", { length: 120 }).notNull(),
  dateOfBirth: timestamp("date_of_birth"),
  sex: mysqlEnum("sex", ["female", "male", "other", "unknown"]).notNull().default("unknown"),
  phone: varchar("phone", { length: 32 }),
  email: varchar("email", { length: 320 }),
  address: text("address"),
  emergencyContact: varchar("emergency_contact", { length: 255 }),
  version: int("version").notNull().default(1),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  uniqueIndex("patients_institution_mrn_unique").on(table.institutionId, table.medicalRecordNumber),
  index("patients_institution_idx").on(table.institutionId),
  index("patients_name_idx").on(table.lastName, table.firstName),
]);

export const patientMedicalRecords = mysqlTable("patient_medical_records", {
  id: int("id").autoincrement().primaryKey(),
  patientId: int("patient_id").notNull().references(() => patients.id, { onDelete: "restrict" }),
  authoredByUserId: int("authored_by_user_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  summary: text("summary").notNull(),
  allergies: text("allergies"),
  chronicConditions: text("chronic_conditions"),
  medications: text("medications"),
  version: int("version").notNull().default(1),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [index("patient_records_patient_idx").on(table.patientId)]);

export const labOrders = mysqlTable("lab_orders", {
  id: int("id").autoincrement().primaryKey(),
  institutionId: int("institution_id").notNull().references(() => institutions.id, { onDelete: "restrict" }),
  laboratoryId: int("laboratory_id").notNull().references(() => laboratories.id, { onDelete: "restrict" }),
  patientId: int("patient_id").notNull().references(() => patients.id, { onDelete: "restrict" }),
  orderingPhysicianId: int("ordering_physician_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  orderNumber: varchar("order_number", { length: 64 }).notNull(),
  priority: mysqlEnum("priority", ["routine", "urgent", "stat"]).notNull().default("routine"),
  clinicalNotes: text("clinical_notes"),
  status: mysqlEnum("status", orderStatusValues).notNull().default("draft"),
  version: int("version").notNull().default(1),
  submittedAt: timestamp("submitted_at"),
  completedAt: timestamp("completed_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  uniqueIndex("lab_orders_institution_number_unique").on(table.institutionId, table.orderNumber),
  index("lab_orders_patient_idx").on(table.patientId),
  index("lab_orders_laboratory_status_idx").on(table.laboratoryId, table.status),
]);

export const labOrderTests = mysqlTable("lab_order_tests", {
  id: int("id").autoincrement().primaryKey(),
  orderId: int("order_id").notNull().references(() => labOrders.id, { onDelete: "restrict" }),
  testCode: varchar("test_code", { length: 64 }).notNull(),
  testNameAr: varchar("test_name_ar", { length: 255 }).notNull(),
  testNameEn: varchar("test_name_en", { length: 255 }).notNull(),
  status: mysqlEnum("status", resultStatusValues).notNull().default("not_started"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [index("lab_order_tests_order_idx").on(table.orderId)]);

export const samples = mysqlTable("samples", {
  id: int("id").autoincrement().primaryKey(),
  orderId: int("order_id").notNull().references(() => labOrders.id, { onDelete: "restrict" }),
  laboratoryId: int("laboratory_id").notNull().references(() => laboratories.id, { onDelete: "restrict" }),
  barcode: varchar("barcode", { length: 128 }).notNull(),
  specimenType: varchar("specimen_type", { length: 100 }).notNull(),
  status: mysqlEnum("status", sampleStatusValues).notNull().default("expected"),
  collectedAt: timestamp("collected_at"),
  receivedAt: timestamp("received_at"),
  verifiedAt: timestamp("verified_at"),
  rejectedReason: text("rejected_reason"),
  version: int("version").notNull().default(1),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  uniqueIndex("samples_laboratory_barcode_unique").on(table.laboratoryId, table.barcode),
  index("samples_order_idx").on(table.orderId),
  index("samples_laboratory_status_idx").on(table.laboratoryId, table.status),
]);

export const sampleStatusEvents = mysqlTable("sample_status_events", {
  id: int("id").autoincrement().primaryKey(),
  sampleId: int("sample_id").notNull().references(() => samples.id, { onDelete: "restrict" }),
  previousStatus: mysqlEnum("previous_status", sampleStatusValues),
  nextStatus: mysqlEnum("next_status", sampleStatusValues).notNull(),
  reason: text("reason"),
  performedByUserId: int("performed_by_user_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  createdAt: timestamp("created_at").defaultNow().notNull(),
}, (table) => [index("sample_events_sample_idx").on(table.sampleId)]);

export const testResults = mysqlTable("test_results", {
  id: int("id").autoincrement().primaryKey(),
  orderTestId: int("order_test_id").notNull().references(() => labOrderTests.id, { onDelete: "restrict" }),
  sampleId: int("sample_id").notNull().references(() => samples.id, { onDelete: "restrict" }),
  value: varchar("value", { length: 255 }),
  unit: varchar("unit", { length: 64 }),
  referenceRange: varchar("reference_range", { length: 255 }),
  interpretation: text("interpretation"),
  isCritical: int("is_critical").notNull().default(0),
  status: mysqlEnum("status", resultStatusValues).notNull().default("not_started"),
  enteredByUserId: int("entered_by_user_id").references(() => users.id, { onDelete: "restrict" }),
  reviewedByUserId: int("reviewed_by_user_id").references(() => users.id, { onDelete: "restrict" }),
  releasedByUserId: int("released_by_user_id").references(() => users.id, { onDelete: "restrict" }),
  enteredAt: timestamp("entered_at"),
  reviewedAt: timestamp("reviewed_at"),
  releasedAt: timestamp("released_at"),
  version: int("version").notNull().default(1),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  uniqueIndex("test_results_order_test_unique").on(table.orderTestId),
  index("test_results_sample_idx").on(table.sampleId),
  index("test_results_status_idx").on(table.status),
]);

export const resultReviewEvents = mysqlTable("result_review_events", {
  id: int("id").autoincrement().primaryKey(),
  resultId: int("result_id").notNull().references(() => testResults.id, { onDelete: "restrict" }),
  previousStatus: mysqlEnum("previous_status", resultStatusValues),
  nextStatus: mysqlEnum("next_status", resultStatusValues).notNull(),
  comment: text("comment"),
  performedByUserId: int("performed_by_user_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  createdAt: timestamp("created_at").defaultNow().notNull(),
}, (table) => [index("result_review_events_result_idx").on(table.resultId)]);

export const criticalAlerts = mysqlTable("critical_alerts", {
  id: int("id").autoincrement().primaryKey(),
  institutionId: int("institution_id").notNull().references(() => institutions.id, { onDelete: "restrict" }),
  resultId: int("result_id").references(() => testResults.id, { onDelete: "restrict" }),
  patientId: int("patient_id").notNull().references(() => patients.id, { onDelete: "restrict" }),
  severity: mysqlEnum("severity", alertSeverityValues).notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  message: text("message").notNull(),
  status: mysqlEnum("status", ["open", "acknowledged", "resolved"]).notNull().default("open"),
  acknowledgedByUserId: int("acknowledged_by_user_id").references(() => users.id, { onDelete: "restrict" }),
  acknowledgedAt: timestamp("acknowledged_at"),
  resolvedAt: timestamp("resolved_at"),
  version: int("version").notNull().default(1),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  index("critical_alerts_institution_status_idx").on(table.institutionId, table.status),
  index("critical_alerts_patient_idx").on(table.patientId),
]);

export const notifications = mysqlTable("notifications", {
  id: int("id").autoincrement().primaryKey(),
  recipientUserId: int("recipient_user_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  alertId: int("alert_id").references(() => criticalAlerts.id, { onDelete: "restrict" }),
  title: varchar("title", { length: 255 }).notNull(),
  message: text("message").notNull(),
  status: mysqlEnum("status", notificationStatusValues).notNull().default("unread"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  readAt: timestamp("read_at"),
}, (table) => [index("notifications_recipient_status_idx").on(table.recipientUserId, table.status)]);

export const universalTasks = mysqlTable("universal_tasks", {
  id: int("id").autoincrement().primaryKey(),
  assigneeUserId: int("assignee_user_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  institutionId: int("institution_id").references(() => institutions.id, { onDelete: "restrict" }),
  title: varchar("title", { length: 255 }).notNull(),
  description: text("description"),
  taskType: varchar("task_type", { length: 80 }).notNull(),
  priority: mysqlEnum("priority", taskPriorityValues).notNull().default("routine"),
  status: mysqlEnum("status", taskStatusValues).notNull().default("pending"),
  entityType: varchar("entity_type", { length: 80 }),
  entityId: varchar("entity_id", { length: 80 }),
  dueAt: timestamp("due_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  index("universal_tasks_assignee_status_idx").on(table.assigneeUserId, table.status),
  index("universal_tasks_institution_idx").on(table.institutionId),
]);

export const approvalRequests = mysqlTable("approval_requests", {
  id: int("id").autoincrement().primaryKey(),
  requesterUserId: int("requester_user_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  reviewerUserId: int("reviewer_user_id").references(() => users.id, { onDelete: "restrict" }),
  institutionId: int("institution_id").references(() => institutions.id, { onDelete: "restrict" }),
  title: varchar("title", { length: 255 }).notNull(),
  description: text("description"),
  entityType: varchar("entity_type", { length: 80 }).notNull(),
  entityId: varchar("entity_id", { length: 80 }).notNull(),
  status: mysqlEnum("status", approvalStatusValues).notNull().default("pending"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  index("approval_requests_reviewer_status_idx").on(table.reviewerUserId, table.status),
  index("approval_requests_institution_idx").on(table.institutionId),
]);

export const systemMessages = mysqlTable("system_messages", {
  id: int("id").autoincrement().primaryKey(),
  recipientUserId: int("recipient_user_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  senderUserId: int("sender_user_id").references(() => users.id, { onDelete: "restrict" }),
  subject: varchar("subject", { length: 255 }).notNull(),
  body: text("body").notNull(),
  status: mysqlEnum("status", notificationStatusValues).notNull().default("unread"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  readAt: timestamp("read_at"),
}, (table) => [index("system_messages_recipient_status_idx").on(table.recipientUserId, table.status)]);

export const auditLog = mysqlTable("audit_log", {
  id: int("id").autoincrement().primaryKey(),
  institutionId: int("institution_id").references(() => institutions.id, { onDelete: "restrict" }),
  actorUserId: int("actor_user_id").references(() => users.id, { onDelete: "restrict" }),
  action: varchar("action", { length: 120 }).notNull(),
  entityType: varchar("entity_type", { length: 80 }).notNull(),
  entityId: varchar("entity_id", { length: 80 }),
  outcome: mysqlEnum("outcome", ["success", "denied", "failure"]).notNull(),
  reason: text("reason"),
  beforeState: json("before_state"),
  afterState: json("after_state"),
  requestId: varchar("request_id", { length: 80 }),
  createdAt: timestamp("created_at").defaultNow().notNull(),
}, (table) => [
  index("audit_log_institution_created_idx").on(table.institutionId, table.createdAt),
  index("audit_log_actor_created_idx").on(table.actorUserId, table.createdAt),
  index("audit_log_entity_idx").on(table.entityType, table.entityId),
]);

export type LisRole = (typeof lisRoleValues)[number];
export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

export const hospitalAdmissions = mysqlTable("hospital_admissions", {
  id: int("id").autoincrement().primaryKey(),
  institutionId: int("institution_id").notNull().references(() => institutions.id, { onDelete: "restrict" }),
  patientId: int("patient_id").notNull().references(() => patients.id, { onDelete: "restrict" }),
  ward: varchar("ward", { length: 100 }).notNull(),
  bedNumber: varchar("bed_number", { length: 32 }).notNull(),
  admittingPhysicianId: int("admitting_physician_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  status: mysqlEnum("status", ["admitted", "transferred", "discharged"]).notNull().default("admitted"),
  admittedAt: timestamp("admitted_at").defaultNow().notNull(),
  dischargedAt: timestamp("discharged_at"),
  notes: text("notes"),
  version: int("version").notNull().default(1),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [index("hospital_admissions_institution_status_idx").on(table.institutionId, table.status)]);

export const clinicConsultations = mysqlTable("clinic_consultations", {
  id: int("id").autoincrement().primaryKey(),
  institutionId: int("institution_id").notNull().references(() => institutions.id, { onDelete: "restrict" }),
  patientId: int("patient_id").notNull().references(() => patients.id, { onDelete: "restrict" }),
  physicianId: int("physician_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  chiefComplaint: text("chief_complaint").notNull(),
  diagnosis: text("diagnosis"),
  soapNotes: text("soap_notes"),
  prescriptionSummary: text("prescription_summary"),
  status: mysqlEnum("status", ["scheduled", "in_progress", "completed", "cancelled"]).notNull().default("scheduled"),
  consultedAt: timestamp("consulted_at").defaultNow().notNull(),
  version: int("version").notNull().default(1),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [index("clinic_consultations_patient_idx").on(table.patientId)]);

export const pharmacyDispensations = mysqlTable("pharmacy_dispensations", {
  id: int("id").autoincrement().primaryKey(),
  institutionId: int("institution_id").notNull().references(() => institutions.id, { onDelete: "restrict" }),
  patientId: int("patient_id").notNull().references(() => patients.id, { onDelete: "restrict" }),
  pharmacistId: int("pharmacist_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  drugName: varchar("drug_name", { length: 255 }).notNull(),
  dosage: varchar("dosage", { length: 120 }).notNull(),
  quantity: int("quantity").notNull().default(1),
  status: mysqlEnum("status", ["prescribed", "dispensed", "cancelled"]).notNull().default("prescribed"),
  dispensedAt: timestamp("dispensed_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [index("pharmacy_dispensations_patient_idx").on(table.patientId)]);

export const radiologyOrders = mysqlTable("radiology_orders", {
  id: int("id").autoincrement().primaryKey(),
  institutionId: int("institution_id").notNull().references(() => institutions.id, { onDelete: "restrict" }),
  patientId: int("patient_id").notNull().references(() => patients.id, { onDelete: "restrict" }),
  orderingPhysicianId: int("ordering_physician_id").notNull().references(() => users.id, { onDelete: "restrict" }),
  modality: varchar("modality", { length: 64 }).notNull(), // X-Ray, CT, MRI, Ultrasound
  bodyPart: varchar("body_part", { length: 120 }).notNull(),
  clinicalIndication: text("clinical_indication"),
  radiologistReport: text("radiologist_report"),
  status: mysqlEnum("status", ["ordered", "imaging_in_progress", "reported", "cancelled"]).notNull().default("ordered"),
  reportedAt: timestamp("reported_at"),
  version: int("version").notNull().default(1),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [index("radiology_orders_patient_idx").on(table.patientId)]);

export const emergencyTriage = mysqlTable("emergency_triage", {
  id: int("id").autoincrement().primaryKey(),
  institutionId: int("institution_id").notNull().references(() => institutions.id, { onDelete: "restrict" }),
  patientId: int("patient_id").notNull().references(() => patients.id, { onDelete: "restrict" }),
  triageLevel: mysqlEnum("triage_level", ["resuscitation", "emergent", "urgent", "less_urgent", "non_urgent"]).notNull().default("urgent"),
  presentingChiefComplaint: text("presenting_chief_complaint").notNull(),
  vitalSignsJson: text("vital_signs_json"),
  disposition: mysqlEnum("disposition", ["admitted", "discharged", "transferred", "deceased"]).notNull().default("admitted"),
  triagedAt: timestamp("triaged_at").defaultNow().notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [index("emergency_triage_institution_idx").on(table.institutionId)]);

export const publicHealthReports = mysqlTable("public_health_reports", {
  id: int("id").autoincrement().primaryKey(),
  institutionId: int("institution_id").notNull().references(() => institutions.id, { onDelete: "restrict" }),
  diseaseCode: varchar("disease_code", { length: 64 }).notNull(),
  diseaseName: varchar("disease_name", { length: 255 }).notNull(),
  confirmedCasesCount: int("confirmed_cases_count").notNull().default(1),
  notes: text("notes"),
  reportedAt: timestamp("reported_at").defaultNow().notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
}, (table) => [index("public_health_reports_institution_idx").on(table.institutionId)]);
