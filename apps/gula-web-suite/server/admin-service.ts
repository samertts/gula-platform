import { and, eq } from "drizzle-orm";
import { TRPCError } from "@trpc/server";
import { laboratories, userRoleAssignments, users } from "../drizzle/schema";
import { getDb } from "./db";
import { writeAudit, type LisActor } from "./lis-service";
import type { LisRole } from "../drizzle/schema";

type AdminActor = LisActor;

function requireAdmin(actor: AdminActor) {
  if (actor.role !== "institution_admin" && actor.role !== "system_admin") {
    throw new TRPCError({ code: "FORBIDDEN", message: "Administrative access is required." });
  }
  if (actor.role !== "system_admin" && !actor.institutionId) {
    throw new TRPCError({ code: "FORBIDDEN", message: "Institution context is required." });
  }
}

export async function getAdminDirectory(actor: AdminActor) {
  requireAdmin(actor);
  const db = await getDb();
  if (!db) throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: "Database is unavailable." });
  const userScope = actor.role === "system_admin" ? undefined : eq(users.institutionId, actor.institutionId!);
  const laboratoryScope = actor.role === "system_admin" ? undefined : eq(laboratories.institutionId, actor.institutionId!);
  const [directoryUsers, directoryLabs] = await Promise.all([
    db.select({ id: users.id, name: users.name, email: users.email, role: users.role, accountStatus: users.accountStatus, laboratoryId: users.laboratoryId, updatedAt: users.updatedAt })
      .from(users).where(userScope).limit(200),
    db.select({ id: laboratories.id, institutionId: laboratories.institutionId, code: laboratories.code, nameAr: laboratories.nameAr, nameEn: laboratories.nameEn, isActive: laboratories.isActive, updatedAt: laboratories.updatedAt })
      .from(laboratories).where(laboratoryScope).limit(100),
  ]);
  return { users: directoryUsers, laboratories: directoryLabs };
}

export async function assignUserRole(actor: AdminActor, input: { userId: number; role: LisRole; laboratoryId?: number; accountStatus?: "active" | "suspended" | "pending" }) {
  requireAdmin(actor);
  const db = await getDb();
  if (!db) throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: "Database is unavailable." });
  const target = (await db.select().from(users).where(eq(users.id, input.userId)).limit(1))[0];
  if (!target) throw new TRPCError({ code: "NOT_FOUND", message: "User not found." });
  if (actor.role !== "system_admin" && target.institutionId !== actor.institutionId) {
    throw new TRPCError({ code: "FORBIDDEN", message: "User is outside organization scope." });
  }
  const institutionId = target.institutionId ?? actor.institutionId;
  if (!institutionId) throw new TRPCError({ code: "BAD_REQUEST", message: "A user must belong to an institution before an operational role is assigned." });
  if (input.laboratoryId) {
    const laboratory = (await db.select().from(laboratories).where(eq(laboratories.id, input.laboratoryId)).limit(1))[0];
    if (!laboratory || laboratory.institutionId !== institutionId) {
      throw new TRPCError({ code: "FORBIDDEN", message: "Laboratory is outside organization scope." });
    }
  }
  return db.transaction(async (tx) => {
    await tx.insert(userRoleAssignments).values({
      userId: target.id,
      institutionId,
      laboratoryId: input.laboratoryId ?? null,
      role: input.role,
      isActive: 1,
      assignedByUserId: actor.id,
    }).onDuplicateKeyUpdate({ set: { isActive: 1, assignedByUserId: actor.id, updatedAt: new Date() } });
    await tx.update(users).set({ role: input.role, laboratoryId: input.laboratoryId ?? target.laboratoryId, accountStatus: input.accountStatus ?? target.accountStatus }).where(eq(users.id, target.id));
    await writeAudit(tx, {
      institutionId,
      actorUserId: actor.id,
      action: "admin.user_role.assign",
      entityType: "user",
      entityId: target.id,
      outcome: "success",
      beforeState: { role: target.role, laboratoryId: target.laboratoryId, accountStatus: target.accountStatus },
      afterState: { role: input.role, laboratoryId: input.laboratoryId ?? target.laboratoryId, accountStatus: input.accountStatus ?? target.accountStatus },
    });
    return { id: target.id, role: input.role };
  });
}

export async function setLaboratoryStatus(actor: AdminActor, laboratoryId: number, isActive: boolean) {
  requireAdmin(actor);
  const db = await getDb();
  if (!db) throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: "Database is unavailable." });
  const laboratory = (await db.select().from(laboratories).where(eq(laboratories.id, laboratoryId)).limit(1))[0];
  if (!laboratory) throw new TRPCError({ code: "NOT_FOUND", message: "Laboratory not found." });
  if (actor.role !== "system_admin" && laboratory.institutionId !== actor.institutionId) {
    throw new TRPCError({ code: "FORBIDDEN", message: "Laboratory is outside organization scope." });
  }
  await db.transaction(async (tx) => {
    await tx.update(laboratories).set({ isActive: isActive ? 1 : 0 }).where(eq(laboratories.id, laboratoryId));
    await writeAudit(tx, {
      institutionId: laboratory.institutionId,
      actorUserId: actor.id,
      action: "admin.laboratory.status",
      entityType: "laboratory",
      entityId: laboratory.id,
      outcome: "success",
      beforeState: { isActive: laboratory.isActive },
      afterState: { isActive: isActive ? 1 : 0 },
    });
  });
  return { id: laboratoryId, isActive };
}

export async function createLaboratory(actor: AdminActor, input: { institutionId?: number; code: string; nameAr: string; nameEn: string; address?: string }) {
  requireAdmin(actor);
  const db = await getDb();
  if (!db) throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: "Database is unavailable." });
  const institutionId = actor.role === "system_admin" ? input.institutionId ?? actor.institutionId : actor.institutionId;
  if (!institutionId) throw new TRPCError({ code: "BAD_REQUEST", message: "Institution context is required." });
  return db.transaction(async (tx) => {
    const result = await tx.insert(laboratories).values({
      institutionId,
      code: input.code,
      nameAr: input.nameAr,
      nameEn: input.nameEn,
      address: input.address ?? null,
      isActive: 1,
    });
    const id = Number(result[0].insertId);
    await writeAudit(tx, {
      institutionId,
      actorUserId: actor.id,
      action: "admin.laboratory.create",
      entityType: "laboratory",
      entityId: id,
      outcome: "success",
      afterState: input,
    });
    return { id };
  });
}

export async function updateLaboratory(actor: AdminActor, input: { id: number; code: string; nameAr: string; nameEn: string; address?: string; isActive: boolean }) {
  requireAdmin(actor);
  const db = await getDb();
  if (!db) throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: "Database is unavailable." });
  const laboratory = (await db.select().from(laboratories).where(eq(laboratories.id, input.id)).limit(1))[0];
  if (!laboratory) throw new TRPCError({ code: "NOT_FOUND", message: "Laboratory not found." });
  if (actor.role !== "system_admin" && laboratory.institutionId !== actor.institutionId) {
    throw new TRPCError({ code: "FORBIDDEN", message: "Laboratory is outside organization scope." });
  }
  await db.transaction(async (tx) => {
    await tx.update(laboratories).set({ code: input.code, nameAr: input.nameAr, nameEn: input.nameEn, address: input.address ?? null, isActive: input.isActive ? 1 : 0 }).where(eq(laboratories.id, input.id));
    await writeAudit(tx, {
      institutionId: laboratory.institutionId,
      actorUserId: actor.id,
      action: "admin.laboratory.update",
      entityType: "laboratory",
      entityId: laboratory.id,
      outcome: "success",
      beforeState: laboratory,
      afterState: input,
    });
  });
  return { id: input.id };
}
