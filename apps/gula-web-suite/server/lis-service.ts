import { TRPCError } from "@trpc/server";
import { and, eq } from "drizzle-orm";
import {
  auditLog,
  labOrderTests,
  labOrders,
  laboratories,
  patientMedicalRecords,
  patients,
  resultReviewEvents,
  sampleStatusEvents,
  samples,
  testResults,
} from "../drizzle/schema";
import { hasPermission, orderTransitions, resultTransitions, sampleTransitions, type LisPermission } from "../shared/lis-policy";
import { getDb } from "./db";

// The service accepts both the root Drizzle client and its transaction handle.
type Db = any;
export type LisActor = { id: number; role: string; institutionId: number | null; laboratoryId: number | null };

type PatientInput = {
  institutionId?: number;
  linkedUserId?: number;
  medicalRecordNumber: string;
  nationalId?: string;
  firstName: string;
  lastName: string;
  dateOfBirth?: Date;
  sex: "female" | "male" | "other" | "unknown";
  phone?: string;
  email?: string;
  address?: string;
  emergencyContact?: string;
};

type OrderInput = {
  institutionId?: number;
  laboratoryId: number;
  patientId: number;
  orderNumber: string;
  priority: "routine" | "urgent" | "stat";
  clinicalNotes?: string;
  tests: Array<{ testCode: string; testNameAr: string; testNameEn: string }>;
};

type AuditArgs = {
  institutionId: number | null;
  actorUserId: number | null;
  action: string;
  entityType: string;
  entityId?: number | string;
  outcome: "success" | "denied" | "failure";
  reason?: string;
  beforeState?: unknown;
  afterState?: unknown;
};

async function dbOrThrow() {
  const db = await getDb();
  if (!db) throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: "Database is unavailable" });
  return db;
}

export async function writeAudit(db: Db, args: AuditArgs) {
  await db.insert(auditLog).values({
    institutionId: args.institutionId,
    actorUserId: args.actorUserId,
    action: args.action,
    entityType: args.entityType,
    entityId: args.entityId === undefined ? null : String(args.entityId),
    outcome: args.outcome,
    reason: args.reason ?? null,
    beforeState: args.beforeState === undefined ? null : args.beforeState,
    afterState: args.afterState === undefined ? null : args.afterState,
  });
}

async function deny(db: Db, actor: LisActor, action: string, entityType: string, entityId: number | string | undefined, reason: string): Promise<never> {
  await writeAudit(db, {
    institutionId: actor.institutionId,
    actorUserId: actor.id,
    action,
    entityType,
    entityId,
    outcome: "denied",
    reason,
  });
  throw new TRPCError({ code: "FORBIDDEN", message: reason });
}

async function requirePermission(db: Db, actor: LisActor, permission: LisPermission, action: string, entityType: string, entityId?: number | string) {
  if (!hasPermission([actor.role], permission)) {
    return deny(db, actor, action, entityType, entityId, `Permission denied: ${permission}`);
  }
}

function scopedInstitution(actor: LisActor, requestedInstitutionId?: number) {
  if (actor.role === "system_admin") return requestedInstitutionId ?? actor.institutionId;
  if (!actor.institutionId) throw new TRPCError({ code: "FORBIDDEN", message: "Organization context is required" });
  if (requestedInstitutionId !== undefined && requestedInstitutionId !== actor.institutionId) {
    throw new TRPCError({ code: "FORBIDDEN", message: "Cross-organization access is not authorized" });
  }
  return actor.institutionId;
}

async function getPatientInScope(db: Db, actor: LisActor, patientId: number) {
  const patient = (await db.select().from(patients).where(eq(patients.id, patientId)).limit(1))[0];
  if (!patient) throw new TRPCError({ code: "NOT_FOUND", message: "Patient not found" });
  if (actor.role === "patient" && patient.linkedUserId !== actor.id) throw new TRPCError({ code: "FORBIDDEN", message: "Patient is outside account scope" });
  if (actor.role !== "system_admin" && actor.institutionId !== patient.institutionId) throw new TRPCError({ code: "FORBIDDEN", message: "Patient is outside organization scope" });
  return patient;
}

async function getOrderInScope(db: Db, actor: LisActor, orderId: number) {
  const order = (await db.select().from(labOrders).where(eq(labOrders.id, orderId)).limit(1))[0];
  if (!order) throw new TRPCError({ code: "NOT_FOUND", message: "Laboratory order not found" });
  if (actor.role === "physician" && order.orderingPhysicianId !== actor.id) throw new TRPCError({ code: "FORBIDDEN", message: "Order is outside physician scope" });
  if (actor.role === "patient") {
    const patient = await getPatientInScope(db, actor, order.patientId);
    if (patient.linkedUserId !== actor.id) throw new TRPCError({ code: "FORBIDDEN", message: "Order is outside patient scope" });
  }
  if (actor.role !== "system_admin" && actor.institutionId !== order.institutionId) throw new TRPCError({ code: "FORBIDDEN", message: "Order is outside organization scope" });
  return order;
}

async function getSampleInScope(db: Db, actor: LisActor, sampleId: number) {
  const sample = (await db.select().from(samples).where(eq(samples.id, sampleId)).limit(1))[0];
  if (!sample) throw new TRPCError({ code: "NOT_FOUND", message: "Sample not found" });
  const laboratory = (await db.select().from(laboratories).where(eq(laboratories.id, sample.laboratoryId)).limit(1))[0];
  if (!laboratory) throw new TRPCError({ code: "NOT_FOUND", message: "Laboratory not found" });
  if (actor.role !== "system_admin" && actor.institutionId !== laboratory.institutionId) throw new TRPCError({ code: "FORBIDDEN", message: "Sample is outside organization scope" });
  if (actor.laboratoryId && actor.laboratoryId !== sample.laboratoryId) throw new TRPCError({ code: "FORBIDDEN", message: "Sample is outside laboratory scope" });
  return { sample, laboratory };
}

export async function createPatient(actor: LisActor, input: PatientInput) {
  const db = await dbOrThrow();
  await requirePermission(db, actor, "patient.create", "patient.create", "patient");
  const institutionId = scopedInstitution(actor, input.institutionId);
  if (!institutionId) throw new TRPCError({ code: "BAD_REQUEST", message: "Institution context is required" });
  return db.transaction(async (tx) => {
    const result = await tx.insert(patients).values({ ...input, institutionId, linkedUserId: input.linkedUserId ?? null, dateOfBirth: input.dateOfBirth ?? null, nationalId: input.nationalId ?? null, phone: input.phone ?? null, email: input.email ?? null, address: input.address ?? null, emergencyContact: input.emergencyContact ?? null });
    const patientId = Number(result[0].insertId);
    await writeAudit(tx, { institutionId, actorUserId: actor.id, action: "patient.create", entityType: "patient", entityId: patientId, outcome: "success", afterState: input });
    return { id: patientId };
  });
}

export async function updatePatient(actor: LisActor, input: PatientInput & { id: number; version: number }) {
  const db = await dbOrThrow();
  await requirePermission(db, actor, "patient.update", "patient.update", "patient", input.id);
  const current = await getPatientInScope(db, actor, input.id);
  if (current.version !== input.version) {
    await writeAudit(db, { institutionId: current.institutionId, actorUserId: actor.id, action: "patient.update", entityType: "patient", entityId: input.id, outcome: "failure", reason: "Stale version conflict", beforeState: current });
    throw new TRPCError({ code: "CONFLICT", message: "Patient changed since it was loaded" });
  }
  const institutionId = current.institutionId;
  const nextVersion = current.version + 1;
  await db.transaction(async (tx) => {
    await tx.update(patients).set({ ...input, id: undefined, version: nextVersion, institutionId: undefined }).where(and(eq(patients.id, input.id), eq(patients.version, input.version)));
    await writeAudit(tx, { institutionId, actorUserId: actor.id, action: "patient.update", entityType: "patient", entityId: input.id, outcome: "success", beforeState: current, afterState: { ...input, version: nextVersion } });
  });
  return { id: input.id, version: nextVersion };
}

export async function createLabOrder(actor: LisActor, input: OrderInput) {
  const db = await dbOrThrow();
  await requirePermission(db, actor, "lab_order.create", "lab_order.create", "lab_order", input.patientId);
  if (actor.role !== "physician" && actor.role !== "system_admin") await deny(db, actor, "lab_order.create", "lab_order", input.patientId, "Only an authorized physician or system administrator may create orders");
  const patient = await getPatientInScope(db, actor, input.patientId);
  const institutionId = scopedInstitution(actor, input.institutionId) ?? patient.institutionId;
  if (institutionId !== patient.institutionId) throw new TRPCError({ code: "FORBIDDEN", message: "Order and patient must share the same organization" });
  const laboratory = (await db.select().from(laboratories).where(eq(laboratories.id, input.laboratoryId)).limit(1))[0];
  if (!laboratory || laboratory.institutionId !== institutionId) throw new TRPCError({ code: "FORBIDDEN", message: "Laboratory is outside organization scope" });
  if (actor.laboratoryId && actor.laboratoryId !== input.laboratoryId) throw new TRPCError({ code: "FORBIDDEN", message: "Laboratory is outside actor scope" });
  return db.transaction(async (tx) => {
    const orderResult = await tx.insert(labOrders).values({ institutionId, laboratoryId: input.laboratoryId, patientId: input.patientId, orderingPhysicianId: actor.id, orderNumber: input.orderNumber, priority: input.priority, clinicalNotes: input.clinicalNotes ?? null, status: "draft", version: 1 });
    const orderId = Number(orderResult[0].insertId);
    if (input.tests.length === 0) throw new TRPCError({ code: "BAD_REQUEST", message: "At least one laboratory test is required" });
    await tx.insert(labOrderTests).values(input.tests.map((test) => ({ orderId, testCode: test.testCode, testNameAr: test.testNameAr, testNameEn: test.testNameEn, status: "not_started" as const })));
    await writeAudit(tx, { institutionId, actorUserId: actor.id, action: "lab_order.create", entityType: "lab_order", entityId: orderId, outcome: "success", afterState: input });
    return { id: orderId };
  });
}

export async function transitionOrder(actor: LisActor, input: { id: number; version: number; nextStatus: keyof typeof orderTransitions }) {
  const db = await dbOrThrow();
  const current = await getOrderInScope(db, actor, input.id);
  const allowed = orderTransitions[current.status as keyof typeof orderTransitions] as readonly string[];
  if (!allowed.includes(input.nextStatus)) {
    await writeAudit(db, { institutionId: current.institutionId, actorUserId: actor.id, action: "lab_order.transition", entityType: "lab_order", entityId: input.id, outcome: "denied", reason: `Invalid transition ${current.status} -> ${input.nextStatus}`, beforeState: current });
    throw new TRPCError({ code: "BAD_REQUEST", message: "Invalid order state transition" });
  }
  if (input.nextStatus === "submitted" && actor.role !== "physician" && actor.role !== "system_admin") await deny(db, actor, "lab_order.transition", "lab_order", input.id, "Only the ordering physician or system administrator may submit an order");
  if (["in_progress", "result_pending_review"].includes(input.nextStatus) && !["lab_staff", "institution_admin", "system_admin"].includes(actor.role)) await deny(db, actor, "lab_order.transition", "lab_order", input.id, "Laboratory workflow transition requires laboratory staff authorization");
  if (input.nextStatus === "completed" && !["physician", "institution_admin", "system_admin"].includes(actor.role)) await deny(db, actor, "lab_order.transition", "lab_order", input.id, "Only an authorized reviewer may complete an order");
  if (current.version !== input.version) throw new TRPCError({ code: "CONFLICT", message: "Order changed since it was loaded" });
  const update: Record<string, unknown> = { status: input.nextStatus, version: current.version + 1 };
  if (input.nextStatus === "submitted") update.submittedAt = new Date();
  if (input.nextStatus === "completed") update.completedAt = new Date();
  await db.transaction(async (tx) => {
    await tx.update(labOrders).set(update).where(and(eq(labOrders.id, input.id), eq(labOrders.version, input.version)));
    await writeAudit(tx, { institutionId: current.institutionId, actorUserId: actor.id, action: "lab_order.transition", entityType: "lab_order", entityId: input.id, outcome: "success", beforeState: current, afterState: { status: input.nextStatus, version: current.version + 1 } });
  });
  return { id: input.id, status: input.nextStatus, version: current.version + 1 };
}

export async function registerSample(actor: LisActor, input: { orderId: number; laboratoryId: number; barcode: string; specimenType: string }) {
  const db = await dbOrThrow();
  await requirePermission(db, actor, "sample.receive", "sample.register", "sample", input.orderId);
  if (!["lab_staff", "institution_admin", "system_admin"].includes(actor.role)) await deny(db, actor, "sample.register", "sample", input.orderId, "Only laboratory staff may register samples");
  const order = await getOrderInScope(db, actor, input.orderId);
  const laboratory = (await db.select().from(laboratories).where(eq(laboratories.id, input.laboratoryId)).limit(1))[0];
  if (!laboratory || laboratory.institutionId !== order.institutionId) throw new TRPCError({ code: "FORBIDDEN", message: "Laboratory is outside order organization" });
  if (actor.laboratoryId && actor.laboratoryId !== input.laboratoryId) throw new TRPCError({ code: "FORBIDDEN", message: "Laboratory is outside actor scope" });
  return db.transaction(async (tx) => {
    const result = await tx.insert(samples).values({ orderId: input.orderId, laboratoryId: input.laboratoryId, barcode: input.barcode, specimenType: input.specimenType, status: "expected", version: 1 });
    const sampleId = Number(result[0].insertId);
    await writeAudit(tx, { institutionId: order.institutionId, actorUserId: actor.id, action: "sample.register", entityType: "sample", entityId: sampleId, outcome: "success", afterState: input });
    return { id: sampleId };
  });
}

export async function transitionSample(actor: LisActor, input: { id: number; version: number; nextStatus: keyof typeof sampleTransitions; reason?: string }) {
  const db = await dbOrThrow();
  await requirePermission(db, actor, input.nextStatus === "received" ? "sample.receive" : input.nextStatus === "verified" ? "sample.verify" : "specimen.process", "sample.transition", "sample", input.id);
  const { sample } = await getSampleInScope(db, actor, input.id);
  const allowed = sampleTransitions[sample.status as keyof typeof sampleTransitions] as readonly string[];
  if (!allowed.includes(input.nextStatus)) {
    await writeAudit(db, { institutionId: actor.institutionId, actorUserId: actor.id, action: "sample.transition", entityType: "sample", entityId: input.id, outcome: "denied", reason: `Invalid transition ${sample.status} -> ${input.nextStatus}`, beforeState: sample });
    throw new TRPCError({ code: "BAD_REQUEST", message: "Invalid sample state transition" });
  }
  if (sample.version !== input.version) throw new TRPCError({ code: "CONFLICT", message: "Sample changed since it was loaded" });
  const timeField = input.nextStatus === "received" ? { receivedAt: new Date() } : input.nextStatus === "verified" ? { verifiedAt: new Date() } : {};
  const nextVersion = sample.version + 1;
  await db.transaction(async (tx) => {
    await tx.update(samples).set({ status: input.nextStatus, version: nextVersion, rejectedReason: input.reason ?? null, ...timeField }).where(and(eq(samples.id, input.id), eq(samples.version, input.version)));
    await tx.insert(sampleStatusEvents).values({ sampleId: input.id, previousStatus: sample.status, nextStatus: input.nextStatus, reason: input.reason ?? null, performedByUserId: actor.id });
    await writeAudit(tx, { institutionId: actor.institutionId, actorUserId: actor.id, action: "sample.transition", entityType: "sample", entityId: input.id, outcome: "success", beforeState: sample, afterState: { status: input.nextStatus, version: nextVersion } });
  });
  return { id: input.id, status: input.nextStatus, version: nextVersion };
}

export async function enterResult(actor: LisActor, input: { orderTestId: number; sampleId: number; value?: string; unit?: string; referenceRange?: string; interpretation?: string; isCritical?: boolean }) {
  const db = await dbOrThrow();
  await requirePermission(db, actor, "result.enter", "result.enter", "test_result", input.orderTestId);
  if (!["lab_staff", "institution_admin", "system_admin"].includes(actor.role)) await deny(db, actor, "result.enter", "test_result", input.orderTestId, "Only laboratory staff may enter results");
  const { sample } = await getSampleInScope(db, actor, input.sampleId);
  if (!["verified", "processing"].includes(sample.status)) throw new TRPCError({ code: "BAD_REQUEST", message: "Result entry requires a verified sample" });
  const orderTest = (await db.select().from(labOrderTests).where(eq(labOrderTests.id, input.orderTestId)).limit(1))[0];
  if (!orderTest) throw new TRPCError({ code: "NOT_FOUND", message: "Order test not found" });
  const order = await getOrderInScope(db, actor, orderTest.orderId);
  const existing = (await db.select().from(testResults).where(eq(testResults.orderTestId, input.orderTestId)).limit(1))[0];
  if (existing && existing.status === "released") throw new TRPCError({ code: "CONFLICT", message: "Released results cannot be overwritten" });
  return db.transaction(async (tx) => {
    let resultId: number;
    if (existing) {
      if (existing.version !== 1 && existing.status !== "rejected") throw new TRPCError({ code: "CONFLICT", message: "Result requires explicit conflict resolution" });
      await tx.update(testResults).set({ sampleId: input.sampleId, value: input.value ?? null, unit: input.unit ?? null, referenceRange: input.referenceRange ?? null, interpretation: input.interpretation ?? null, isCritical: input.isCritical ? 1 : 0, status: "entered", enteredByUserId: actor.id, enteredAt: new Date(), version: existing.version + 1 }).where(and(eq(testResults.id, existing.id), eq(testResults.version, existing.version)));
      resultId = existing.id;
    } else {
      const inserted = await tx.insert(testResults).values({ orderTestId: input.orderTestId, sampleId: input.sampleId, value: input.value ?? null, unit: input.unit ?? null, referenceRange: input.referenceRange ?? null, interpretation: input.interpretation ?? null, isCritical: input.isCritical ? 1 : 0, status: "entered", enteredByUserId: actor.id, enteredAt: new Date(), version: 1 });
      resultId = Number(inserted[0].insertId);
    }
    await writeAudit(tx, { institutionId: order.institutionId, actorUserId: actor.id, action: "result.enter", entityType: "test_result", entityId: resultId, outcome: "success", afterState: input });
    return { id: resultId, status: "entered" as const };
  });
}

export async function transitionResult(actor: LisActor, input: { id: number; version: number; nextStatus: keyof typeof resultTransitions; comment?: string }) {
  const db = await dbOrThrow();
  const result = (await db.select().from(testResults).where(eq(testResults.id, input.id)).limit(1))[0];
  if (!result) throw new TRPCError({ code: "NOT_FOUND", message: "Result not found" });
  const { sample } = await getSampleInScope(db, actor, result.sampleId);
  const orderTest = (await db.select().from(labOrderTests).where(eq(labOrderTests.id, result.orderTestId)).limit(1))[0];
  if (!orderTest) throw new TRPCError({ code: "NOT_FOUND", message: "Order test not found" });
  const order = await getOrderInScope(db, actor, orderTest.orderId);
  const allowed = resultTransitions[result.status as keyof typeof resultTransitions] as readonly string[];
  if (!allowed.includes(input.nextStatus)) {
    await writeAudit(db, { institutionId: order.institutionId, actorUserId: actor.id, action: "result.transition", entityType: "test_result", entityId: input.id, outcome: "denied", reason: `Invalid transition ${result.status} -> ${input.nextStatus}`, beforeState: result });
    throw new TRPCError({ code: "BAD_REQUEST", message: "Invalid result state transition" });
  }
  if (input.nextStatus === "approved" || input.nextStatus === "rejected") {
    await requirePermission(db, actor, "result.review", "result.transition", "test_result", input.id);
    if (!["physician", "institution_admin", "system_admin"].includes(actor.role)) await deny(db, actor, "result.transition", "test_result", input.id, "Result review requires an authorized senior role");
  }
  if (input.nextStatus === "released") {
    await requirePermission(db, actor, "result.release", "result.transition", "test_result", input.id);
    if (result.status !== "approved") throw new TRPCError({ code: "BAD_REQUEST", message: "Only approved results may be released" });
  }
  if (result.version !== input.version) throw new TRPCError({ code: "CONFLICT", message: "Result changed since it was loaded" });
  const nextVersion = result.version + 1;
  await db.transaction(async (tx) => {
    await tx.update(testResults).set({ status: input.nextStatus, version: nextVersion, reviewedByUserId: ["approved", "rejected"].includes(input.nextStatus) ? actor.id : result.reviewedByUserId, reviewedAt: ["approved", "rejected"].includes(input.nextStatus) ? new Date() : result.reviewedAt, releasedByUserId: input.nextStatus === "released" ? actor.id : result.releasedByUserId, releasedAt: input.nextStatus === "released" ? new Date() : result.releasedAt }).where(and(eq(testResults.id, input.id), eq(testResults.version, input.version)));
    await tx.insert(resultReviewEvents).values({ resultId: input.id, previousStatus: result.status, nextStatus: input.nextStatus, comment: input.comment ?? null, performedByUserId: actor.id });
    await writeAudit(tx, { institutionId: order.institutionId, actorUserId: actor.id, action: "result.transition", entityType: "test_result", entityId: input.id, outcome: "success", beforeState: result, afterState: { status: input.nextStatus, version: nextVersion, sampleStatus: sample.status } });
  });
  return { id: input.id, status: input.nextStatus, version: nextVersion };
}

export async function addMedicalRecord(actor: LisActor, input: { patientId: number; summary: string; allergies?: string; chronicConditions?: string; medications?: string }) {
  const db = await dbOrThrow();
  await requirePermission(db, actor, "patient.update", "medical_record.create", "patient_medical_record", input.patientId);
  const patient = await getPatientInScope(db, actor, input.patientId);
  if (!["physician", "institution_admin", "system_admin"].includes(actor.role)) await deny(db, actor, "medical_record.create", "patient_medical_record", input.patientId, "Medical record entry requires an authorized clinician or administrator");
  return db.transaction(async (tx) => {
    const inserted = await tx.insert(patientMedicalRecords).values({ patientId: input.patientId, authoredByUserId: actor.id, summary: input.summary, allergies: input.allergies ?? null, chronicConditions: input.chronicConditions ?? null, medications: input.medications ?? null, version: 1 });
    const id = Number(inserted[0].insertId);
    await writeAudit(tx, { institutionId: patient.institutionId, actorUserId: actor.id, action: "medical_record.create", entityType: "patient_medical_record", entityId: id, outcome: "success", afterState: input });
    return { id };
  });
}
