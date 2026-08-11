import { and, count, desc, eq, or } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import {
  approvalRequests,
  auditLog,
  clinicConsultations,
  criticalAlerts,
  emergencyTriage,
  hospitalAdmissions,
  institutions,
  labOrders,
  labOrderTests,
  laboratories,
  notifications,
  patients,
  patientMedicalRecords,
  pharmacyDispensations,
  radiologyOrders,
  samples,
  systemMessages,
  testResults,
  universalTasks,
  userRoleAssignments,
  users,
  type InsertUser,
  type User,
} from "../drizzle/schema";
import { ENV } from "./_core/env";

let _db: ReturnType<typeof drizzle> | null = null;

export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) throw new Error("User openId is required for upsert");
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  const values: InsertUser = { openId: user.openId };
  const updateSet: Record<string, unknown> = {};
  const textFields = ["name", "email", "loginMethod"] as const;

  for (const field of textFields) {
    const value = user[field];
    if (value !== undefined) {
      values[field] = value ?? null;
      updateSet[field] = value ?? null;
    }
  }

  if (user.lastSignedIn !== undefined) {
    values.lastSignedIn = user.lastSignedIn;
    updateSet.lastSignedIn = user.lastSignedIn;
  }
  if (user.role !== undefined) {
    values.role = user.role;
    updateSet.role = user.role;
  } else if (user.openId === ENV.ownerOpenId) {
    values.role = "system_admin";
    values.accountStatus = "active";
    updateSet.role = "system_admin";
    updateSet.accountStatus = "active";
  }

  if (!values.lastSignedIn) values.lastSignedIn = new Date();
  if (Object.keys(updateSet).length === 0) updateSet.lastSignedIn = new Date();

  await db.insert(users).values(values).onDuplicateKeyUpdate({ set: updateSet });
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) return undefined;
  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);
  return result[0];
}

export async function getUserRoles(userId: number, fallbackRole: User["role"]) {
  const db = await getDb();
  if (!db || userId < 0) return [fallbackRole];
  const assignments = await db
    .select({ role: userRoleAssignments.role })
    .from(userRoleAssignments)
    .where(and(eq(userRoleAssignments.userId, userId), eq(userRoleAssignments.isActive, 1)))
    .limit(20);
  return Array.from(new Set([fallbackRole, ...assignments.map((row) => row.role)]));
}

export async function getInstitutionContext(institutionId: number | null, laboratoryId: number | null) {
  const db = await getDb();
  if (!db) return { institution: null, laboratory: null };
  const institution = institutionId
    ? (await db.select({ id: institutions.id, code: institutions.code, nameAr: institutions.nameAr, nameEn: institutions.nameEn }).from(institutions).where(eq(institutions.id, institutionId)).limit(1))[0] ?? null
    : null;
  const laboratory = laboratoryId
    ? (await db.select({ id: laboratories.id, code: laboratories.code, nameAr: laboratories.nameAr, nameEn: laboratories.nameEn }).from(laboratories).where(eq(laboratories.id, laboratoryId)).limit(1))[0] ?? null
    : null;
  return { institution, laboratory };
}

export async function getDashboardCounts(institutionId: number | null) {
  const db = await getDb();
  if (!db) return null;
  const [orders, sampleRows, pendingResults, alerts] = await Promise.all([
    institutionId
      ? db.select({ total: count() }).from(labOrders).where(eq(labOrders.institutionId, institutionId))
      : db.select({ total: count() }).from(labOrders),
    institutionId
      ? db.select({ total: count() }).from(samples).innerJoin(labOrders, eq(samples.orderId, labOrders.id)).where(eq(labOrders.institutionId, institutionId))
      : db.select({ total: count() }).from(samples),
    institutionId
      ? db.select({ total: count() }).from(testResults).innerJoin(samples, eq(testResults.sampleId, samples.id)).innerJoin(laboratories, eq(samples.laboratoryId, laboratories.id)).where(and(eq(testResults.status, "pending_review"), eq(laboratories.institutionId, institutionId)))
      : db.select({ total: count() }).from(testResults).where(eq(testResults.status, "pending_review")),
    institutionId
      ? db.select({ total: count() }).from(criticalAlerts).where(and(eq(criticalAlerts.institutionId, institutionId), eq(criticalAlerts.status, "open")))
      : db.select({ total: count() }).from(criticalAlerts).where(eq(criticalAlerts.status, "open")),
  ]);

  return {
    orders: Number(orders[0]?.total ?? 0),
    samples: Number(sampleRows[0]?.total ?? 0),
    pendingResults: Number(pendingResults[0]?.total ?? 0),
    criticalAlerts: Number(alerts[0]?.total ?? 0),
  };
}

export async function getRecentActivity(institutionId: number | null) {
  const db = await getDb();
  if (!db) return [];
  const rows = await db
    .select({
      id: auditLog.id,
      action: auditLog.action,
      entityType: auditLog.entityType,
      outcome: auditLog.outcome,
      createdAt: auditLog.createdAt,
    })
    .from(auditLog)
    .where(institutionId ? eq(auditLog.institutionId, institutionId) : undefined)
    .orderBy(desc(auditLog.createdAt))
    .limit(8);
  return rows;
}

export async function getScopedNotifications(userId: number) {
  const db = await getDb();
  if (!db || userId < 0) return [];
  return db
    .select({ id: notifications.id, title: notifications.title, message: notifications.message, status: notifications.status, createdAt: notifications.createdAt })
    .from(notifications)
    .where(eq(notifications.recipientUserId, userId))
    .orderBy(desc(notifications.createdAt))
    .limit(20);
}

export async function getScopedInbox(user: ScopedUser) {
  const db = await getDb();
  if (!db || user.id < 0) return { notifications: [], tasks: [], alerts: [], approvals: [], messages: [] };
  const institutionCondition = user.institutionId ? eq(universalTasks.institutionId, user.institutionId) : undefined;
  const [notificationsRows, tasksRows, approvalsRows, messagesRows, alertsRows] = await Promise.all([
    getScopedNotifications(user.id),
    db.select({ id: universalTasks.id, title: universalTasks.title, description: universalTasks.description, taskType: universalTasks.taskType, priority: universalTasks.priority, status: universalTasks.status, entityType: universalTasks.entityType, entityId: universalTasks.entityId, dueAt: universalTasks.dueAt, createdAt: universalTasks.createdAt })
      .from(universalTasks)
      .where(institutionCondition ? and(eq(universalTasks.assigneeUserId, user.id), institutionCondition) : eq(universalTasks.assigneeUserId, user.id))
      .orderBy(desc(universalTasks.createdAt)).limit(30),
    db.select({ id: approvalRequests.id, title: approvalRequests.title, description: approvalRequests.description, entityType: approvalRequests.entityType, entityId: approvalRequests.entityId, status: approvalRequests.status, createdAt: approvalRequests.createdAt, updatedAt: approvalRequests.updatedAt })
      .from(approvalRequests)
      .where(
        user.role === "institution_admin" || user.role === "system_admin"
          ? user.institutionId
            ? and(eq(approvalRequests.institutionId, user.institutionId), eq(approvalRequests.status, "pending"))
            : eq(approvalRequests.status, "pending")
          : and(eq(approvalRequests.reviewerUserId, user.id), eq(approvalRequests.status, "pending")),
      )
      .orderBy(desc(approvalRequests.createdAt)).limit(30),
    db.select({ id: systemMessages.id, subject: systemMessages.subject, body: systemMessages.body, status: systemMessages.status, createdAt: systemMessages.createdAt, readAt: systemMessages.readAt })
      .from(systemMessages)
      .where(eq(systemMessages.recipientUserId, user.id))
      .orderBy(desc(systemMessages.createdAt)).limit(30),
    user.role === "patient"
      ? db.select({ id: criticalAlerts.id, severity: criticalAlerts.severity, title: criticalAlerts.title, message: criticalAlerts.message, status: criticalAlerts.status, createdAt: criticalAlerts.createdAt })
        .from(criticalAlerts).innerJoin(patients, eq(criticalAlerts.patientId, patients.id))
        .where(and(eq(patients.linkedUserId, user.id), eq(criticalAlerts.status, "open"))).orderBy(desc(criticalAlerts.createdAt)).limit(20)
      : user.institutionId
        ? db.select({ id: criticalAlerts.id, severity: criticalAlerts.severity, title: criticalAlerts.title, message: criticalAlerts.message, status: criticalAlerts.status, createdAt: criticalAlerts.createdAt })
          .from(criticalAlerts).where(and(eq(criticalAlerts.institutionId, user.institutionId), eq(criticalAlerts.status, "open"))).orderBy(desc(criticalAlerts.createdAt)).limit(20)
        : db.select({ id: criticalAlerts.id, severity: criticalAlerts.severity, title: criticalAlerts.title, message: criticalAlerts.message, status: criticalAlerts.status, createdAt: criticalAlerts.createdAt })
          .from(criticalAlerts).where(eq(criticalAlerts.status, "open")).orderBy(desc(criticalAlerts.createdAt)).limit(20),
  ]);
  return { notifications: notificationsRows, tasks: tasksRows, alerts: alertsRows, approvals: approvalsRows, messages: messagesRows };
}

type ScopedUser = { id: number; role: string; institutionId: number | null; laboratoryId: number | null };

export async function getScopedPatients(user: ScopedUser) {
  const db = await getDb();
  if (!db || user.id < 0) return [];
  if (user.role === "patient") {
    return db
      .select({ id: patients.id, medicalRecordNumber: patients.medicalRecordNumber, firstName: patients.firstName, lastName: patients.lastName, sex: patients.sex, updatedAt: patients.updatedAt })
      .from(patients)
      .where(eq(patients.linkedUserId, user.id))
      .orderBy(desc(patients.updatedAt))
      .limit(50);
  }
  if (user.role === "physician") {
    return db
      .select({ id: patients.id, medicalRecordNumber: patients.medicalRecordNumber, firstName: patients.firstName, lastName: patients.lastName, sex: patients.sex, updatedAt: patients.updatedAt })
      .from(patients)
      .innerJoin(labOrders, eq(labOrders.patientId, patients.id))
      .where(eq(labOrders.orderingPhysicianId, user.id))
      .groupBy(patients.id, patients.medicalRecordNumber, patients.firstName, patients.lastName, patients.sex, patients.updatedAt)
      .orderBy(desc(patients.updatedAt))
      .limit(50);
  }
  if (user.institutionId) {
    return db
      .select({ id: patients.id, medicalRecordNumber: patients.medicalRecordNumber, firstName: patients.firstName, lastName: patients.lastName, sex: patients.sex, updatedAt: patients.updatedAt })
      .from(patients)
      .where(eq(patients.institutionId, user.institutionId))
      .orderBy(desc(patients.updatedAt))
      .limit(50);
  }
  if (user.role === "system_admin") {
    return db
      .select({ id: patients.id, medicalRecordNumber: patients.medicalRecordNumber, firstName: patients.firstName, lastName: patients.lastName, sex: patients.sex, updatedAt: patients.updatedAt })
      .from(patients)
      .orderBy(desc(patients.updatedAt))
      .limit(50);
  }
  return [];
}

export async function getScopedOrders(user: ScopedUser) {
  const db = await getDb();
  if (!db || user.id < 0) return [];
  if (user.role === "patient") {
    return db
      .select({ id: labOrders.id, orderNumber: labOrders.orderNumber, priority: labOrders.priority, status: labOrders.status, createdAt: labOrders.createdAt })
      .from(labOrders)
      .innerJoin(patients, eq(labOrders.patientId, patients.id))
      .where(eq(patients.linkedUserId, user.id))
      .orderBy(desc(labOrders.createdAt))
      .limit(50);
  }
  const condition = user.role === "physician"
    ? eq(labOrders.orderingPhysicianId, user.id)
    : user.institutionId
      ? eq(labOrders.institutionId, user.institutionId)
      : user.role === "system_admin"
        ? undefined
        : undefined;
  return db
    .select({ id: labOrders.id, orderNumber: labOrders.orderNumber, priority: labOrders.priority, status: labOrders.status, createdAt: labOrders.createdAt })
    .from(labOrders)
    .where(condition)
    .orderBy(desc(labOrders.createdAt))
    .limit(50);
}

export async function getScopedSamples(user: ScopedUser) {
  const db = await getDb();
  if (!db) return [];
  const condition = user.laboratoryId
    ? eq(samples.laboratoryId, user.laboratoryId)
    : user.institutionId
      ? eq(laboratories.institutionId, user.institutionId)
      : user.role === "system_admin"
        ? undefined
        : undefined;
  if (!condition && user.role !== "system_admin") return [];
  return db
    .select({ id: samples.id, barcode: samples.barcode, specimenType: samples.specimenType, status: samples.status, version: samples.version, updatedAt: samples.updatedAt })
    .from(samples)
    .innerJoin(laboratories, eq(samples.laboratoryId, laboratories.id))
    .where(condition)
    .orderBy(desc(samples.updatedAt))
    .limit(50);
}

export async function getScopedResults(user: ScopedUser) {
  const db = await getDb();
  if (!db || (user.role !== "system_admin" && !user.institutionId && user.role !== "patient" && user.role !== "physician")) return [];
  const base = db
    .select({ id: testResults.id, value: testResults.value, status: testResults.status, isCritical: testResults.isCritical, version: testResults.version, updatedAt: testResults.updatedAt })
    .from(testResults)
    .innerJoin(samples, eq(testResults.sampleId, samples.id))
    .innerJoin(laboratories, eq(samples.laboratoryId, laboratories.id))
    .innerJoin(labOrderTests, eq(testResults.orderTestId, labOrderTests.id))
    .innerJoin(labOrders, eq(labOrderTests.orderId, labOrders.id))
    .innerJoin(patients, eq(labOrders.patientId, patients.id));
  const condition = user.role === "patient"
    ? eq(patients.linkedUserId, user.id)
    : user.role === "physician"
      ? eq(labOrders.orderingPhysicianId, user.id)
      : user.institutionId
        ? eq(laboratories.institutionId, user.institutionId)
        : undefined;
  return base.where(condition).orderBy(desc(testResults.updatedAt)).limit(50);
}

export type PatientTimelineEntry = {
  id: string;
  source: "laboratory" | "clinical" | "alerts" | "radiology" | "pharmacy" | "hospital" | "emergency";
  kind: string;
  title: string;
  detail: string | null;
  status: string;
  isCritical: boolean;
  occurredAt: Date;
};

/**
 * Returns an own-record-only timeline for the authenticated patient.  All
 * source queries join through patients.linkedUserId, so identifiers supplied
 * by a client can never broaden the patient's data scope.
 */
export function sortPatientTimelineEntries(entries: PatientTimelineEntry[]): PatientTimelineEntry[] {
  return [...entries].sort((a, b) => b.occurredAt.getTime() - a.occurredAt.getTime());
}

export async function getPatientUnifiedTimeline(userId: number, institutionId: number | null): Promise<PatientTimelineEntry[]> {
  const db = await getDb();
  if (!db || userId < 0 || !institutionId) return [];
  const patientScope = and(eq(patients.linkedUserId, userId), eq(patients.institutionId, institutionId));

  const [records, orders, results, alerts, consultations, admissions, dispensations, imaging, emergencies] = await Promise.all([
    db.select({
      id: patientMedicalRecords.id,
      summary: patientMedicalRecords.summary,
      updatedAt: patientMedicalRecords.updatedAt,
    })
      .from(patientMedicalRecords)
      .innerJoin(patients, eq(patientMedicalRecords.patientId, patients.id))
      .where(patientScope)
      .orderBy(desc(patientMedicalRecords.updatedAt))
      .limit(100),
    db.select({
      id: labOrders.id,
      orderNumber: labOrders.orderNumber,
      priority: labOrders.priority,
      status: labOrders.status,
      createdAt: labOrders.createdAt,
    })
      .from(labOrders)
      .innerJoin(patients, eq(labOrders.patientId, patients.id))
      .where(and(patientScope, eq(labOrders.institutionId, institutionId)))
      .orderBy(desc(labOrders.createdAt))
      .limit(100),
    db.select({
      id: testResults.id,
      value: testResults.value,
      status: testResults.status,
      isCritical: testResults.isCritical,
      updatedAt: testResults.updatedAt,
      testNameAr: labOrderTests.testNameAr,
      testNameEn: labOrderTests.testNameEn,
    })
      .from(testResults)
      .innerJoin(labOrderTests, eq(testResults.orderTestId, labOrderTests.id))
      .innerJoin(labOrders, eq(labOrderTests.orderId, labOrders.id))
      .innerJoin(patients, eq(labOrders.patientId, patients.id))
      .where(and(patientScope, eq(labOrders.institutionId, institutionId)))
      .orderBy(desc(testResults.updatedAt))
      .limit(100),
    db.select({
      id: criticalAlerts.id,
      severity: criticalAlerts.severity,
      title: criticalAlerts.title,
      message: criticalAlerts.message,
      status: criticalAlerts.status,
      createdAt: criticalAlerts.createdAt,
    })
      .from(criticalAlerts)
      .innerJoin(patients, eq(criticalAlerts.patientId, patients.id))
      .where(and(patientScope, eq(criticalAlerts.institutionId, institutionId)))
      .orderBy(desc(criticalAlerts.createdAt))
      .limit(100),
    db.select({
      id: clinicConsultations.id,
      chiefComplaint: clinicConsultations.chiefComplaint,
      diagnosis: clinicConsultations.diagnosis,
      status: clinicConsultations.status,
      consultedAt: clinicConsultations.consultedAt,
    })
      .from(clinicConsultations)
      .innerJoin(patients, eq(clinicConsultations.patientId, patients.id))
      .where(and(patientScope, eq(clinicConsultations.institutionId, institutionId)))
      .orderBy(desc(clinicConsultations.consultedAt))
      .limit(100),
    db.select({
      id: hospitalAdmissions.id,
      ward: hospitalAdmissions.ward,
      bedNumber: hospitalAdmissions.bedNumber,
      status: hospitalAdmissions.status,
      notes: hospitalAdmissions.notes,
      admittedAt: hospitalAdmissions.admittedAt,
    })
      .from(hospitalAdmissions)
      .innerJoin(patients, eq(hospitalAdmissions.patientId, patients.id))
      .where(and(patientScope, eq(hospitalAdmissions.institutionId, institutionId)))
      .orderBy(desc(hospitalAdmissions.admittedAt))
      .limit(100),
    db.select({
      id: pharmacyDispensations.id,
      drugName: pharmacyDispensations.drugName,
      dosage: pharmacyDispensations.dosage,
      quantity: pharmacyDispensations.quantity,
      status: pharmacyDispensations.status,
      dispensedAt: pharmacyDispensations.dispensedAt,
      createdAt: pharmacyDispensations.createdAt,
    })
      .from(pharmacyDispensations)
      .innerJoin(patients, eq(pharmacyDispensations.patientId, patients.id))
      .where(and(patientScope, eq(pharmacyDispensations.institutionId, institutionId)))
      .orderBy(desc(pharmacyDispensations.createdAt))
      .limit(100),
    db.select({
      id: radiologyOrders.id,
      modality: radiologyOrders.modality,
      bodyPart: radiologyOrders.bodyPart,
      radiologistReport: radiologyOrders.radiologistReport,
      status: radiologyOrders.status,
      reportedAt: radiologyOrders.reportedAt,
      createdAt: radiologyOrders.createdAt,
    })
      .from(radiologyOrders)
      .innerJoin(patients, eq(radiologyOrders.patientId, patients.id))
      .where(and(patientScope, eq(radiologyOrders.institutionId, institutionId)))
      .orderBy(desc(radiologyOrders.createdAt))
      .limit(100),
    db.select({
      id: emergencyTriage.id,
      triageLevel: emergencyTriage.triageLevel,
      presentingChiefComplaint: emergencyTriage.presentingChiefComplaint,
      disposition: emergencyTriage.disposition,
      triagedAt: emergencyTriage.triagedAt,
    })
      .from(emergencyTriage)
      .innerJoin(patients, eq(emergencyTriage.patientId, patients.id))
      .where(and(patientScope, eq(emergencyTriage.institutionId, institutionId)))
      .orderBy(desc(emergencyTriage.triagedAt))
      .limit(100),
  ]);

  const entries: PatientTimelineEntry[] = [
    ...records.map((record) => ({
      id: `clinical-${record.id}`,
      source: "clinical" as const,
      kind: "medical_record",
      title: "Clinical record update",
      detail: record.summary,
      status: "documented",
      isCritical: false,
      occurredAt: record.updatedAt,
    })),
    ...orders.map((order) => ({
      id: `laboratory-order-${order.id}`,
      source: "laboratory" as const,
      kind: "lab_order",
      title: `Laboratory order ${order.orderNumber}`,
      detail: `Priority: ${order.priority}`,
      status: order.status,
      isCritical: order.priority === "stat",
      occurredAt: order.createdAt,
    })),
    ...results.map((result) => ({
      id: `laboratory-result-${result.id}`,
      source: "laboratory" as const,
      kind: "lab_result",
      title: result.testNameAr || result.testNameEn,
      detail: result.value,
      status: result.status,
      isCritical: result.isCritical === 1,
      occurredAt: result.updatedAt,
    })),
    ...alerts.map((alert) => ({
      id: `alert-${alert.id}`,
      source: "alerts" as const,
      kind: "critical_alert",
      title: alert.title,
      detail: alert.message,
      status: alert.status,
      isCritical: alert.severity === "critical",
      occurredAt: alert.createdAt,
    })),
    ...consultations.map((consultation) => ({
      id: `consultation-${consultation.id}`,
      source: "clinical" as const,
      kind: "consultation",
      title: consultation.chiefComplaint,
      detail: consultation.diagnosis,
      status: consultation.status,
      isCritical: false,
      occurredAt: consultation.consultedAt,
    })),
    ...admissions.map((admission) => ({
      id: `admission-${admission.id}`,
      source: "hospital" as const,
      kind: "admission",
      title: `Hospital admission · ${admission.ward}`,
      detail: `${admission.bedNumber}${admission.notes ? ` · ${admission.notes}` : ""}`,
      status: admission.status,
      isCritical: false,
      occurredAt: admission.admittedAt,
    })),
    ...dispensations.map((dispensation) => ({
      id: `pharmacy-${dispensation.id}`,
      source: "pharmacy" as const,
      kind: "dispensation",
      title: dispensation.drugName,
      detail: `${dispensation.dosage} · ${dispensation.quantity}`,
      status: dispensation.status,
      isCritical: false,
      occurredAt: dispensation.dispensedAt ?? dispensation.createdAt,
    })),
    ...imaging.map((study) => ({
      id: `radiology-${study.id}`,
      source: "radiology" as const,
      kind: "imaging",
      title: `${study.modality} · ${study.bodyPart}`,
      detail: study.radiologistReport,
      status: study.status,
      isCritical: false,
      occurredAt: study.reportedAt ?? study.createdAt,
    })),
    ...emergencies.map((emergency) => ({
      id: `emergency-${emergency.id}`,
      source: "emergency" as const,
      kind: "emergency_visit",
      title: emergency.presentingChiefComplaint,
      detail: `Triage: ${emergency.triageLevel} · ${emergency.disposition}`,
      status: emergency.disposition,
      isCritical: ["resuscitation", "emergent"].includes(emergency.triageLevel),
      occurredAt: emergency.triagedAt,
    })),
  ];

  return sortPatientTimelineEntries(entries);
}
