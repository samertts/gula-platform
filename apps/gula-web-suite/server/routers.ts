import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { protectedProcedure, publicProcedure, router } from "./_core/trpc";
import {
  getDashboardCounts,
  getInstitutionContext,
  getRecentActivity,
  getScopedInbox,
  getScopedOrders,
  getPatientUnifiedTimeline,
  getScopedPatients,
  getScopedResults,
  getScopedSamples,
  getUserRoles,
} from "./db";
import {
  addMedicalRecord,
  createLabOrder,
  createPatient,
  enterResult,
  registerSample,
  transitionOrder,
  transitionResult,
  transitionSample,
  updatePatient,
} from "./lis-service";
import {
  canUsePermissionInWorkspace,
  canUseWorkspace,
  discoverWorkspaces,
  permissionCatalog,
  permissionsForRoles,
  roleLabels,
  resultTransitions,
  sampleTransitions,
  workspaceCatalog,
  type LisPermission,
  type WorkspaceId,
} from "../shared/lis-policy";

const workspaceInput = z.object({ workspaceId: z.string().optional() });
const orderStatusInput = z.enum(["submitted", "sample_pending", "in_progress", "result_pending_review", "completed", "cancelled"]);
const sampleStatusInput = z.enum(["received", "verified", "processing", "rejected", "completed"]);
const resultStatusInput = z.enum(["entered", "pending_review", "approved", "released", "rejected"]);

function selectedWorkspace(workspaceId: string | undefined, roles: readonly string[]) {
  const workspaces = discoverWorkspaces(roles);
  const selected = workspaceId ? workspaces.find((item) => item.id === workspaceId) : workspaces[0];
  if (!selected) {
    throw new TRPCError({
      code: "FORBIDDEN",
      message: "Selected workspace is not authorized for this account role.",
    });
  }
  return selected;
}

function actorFromContext(ctx: { user: { id: number; role: string; institutionId: number | null; laboratoryId: number | null } }) {
  return { id: ctx.user.id, role: ctx.user.role, institutionId: ctx.user.institutionId, laboratoryId: ctx.user.laboratoryId };
}

export const appRouter = router({
  system: systemRouter,
  auth: router({
    me: publicProcedure.query((opts) => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return { success: true } as const;
    }),
  }),
  lis: router({
    context: protectedProcedure.query(async ({ ctx }) => {
      const roles = await getUserRoles(ctx.user.id, ctx.user.role);
      const workspaces = discoverWorkspaces(roles);
      const organization = await getInstitutionContext(ctx.user.institutionId, ctx.user.laboratoryId);
      return {
        user: {
          id: ctx.user.id,
          name: ctx.user.name,
          email: ctx.user.email,
          role: ctx.user.role,
          accountStatus: ctx.user.accountStatus,
        },
        roles,
        permissions: permissionsForRoles(roles),
        workspaces,
        organization,
        defaultWorkspaceId: workspaces[0]?.id ?? null,
      };
    }),
    permissions: protectedProcedure.query(async ({ ctx }) => {
      const roles = await getUserRoles(ctx.user.id, ctx.user.role);
      return { roles, permissions: permissionsForRoles(roles), catalog: permissionCatalog };
    }),
    dashboard: protectedProcedure.input(workspaceInput).query(async ({ ctx, input }) => {
      const roles = await getUserRoles(ctx.user.id, ctx.user.role);
      const workspace = selectedWorkspace(input.workspaceId, roles);
      const counts = ctx.user.role === "patient" || ctx.user.role === "physician"
        ? null
        : await getDashboardCounts(ctx.user.institutionId);
      const recentActivity = ctx.user.role === "patient" ? [] : await getRecentActivity(ctx.user.institutionId);
      return {
        workspace: {
          id: workspace.id,
          label: workspace.label,
          description: workspace.description,
          accent: workspace.accent,
          capabilities: workspace.capabilities,
        },
        counts,
        recentActivity,
      };
    }),
    patients: protectedProcedure.input(workspaceInput).query(async ({ ctx, input }) => {
      const roles = await getUserRoles(ctx.user.id, ctx.user.role);
      selectedWorkspace(input.workspaceId, roles);
      return getScopedPatients(ctx.user);
    }),
    orders: protectedProcedure.input(workspaceInput).query(async ({ ctx, input }) => {
      const roles = await getUserRoles(ctx.user.id, ctx.user.role);
      selectedWorkspace(input.workspaceId, roles);
      return getScopedOrders(ctx.user);
    }),
    samples: protectedProcedure.input(workspaceInput).query(async ({ ctx, input }) => {
      const roles = await getUserRoles(ctx.user.id, ctx.user.role);
      const workspace = selectedWorkspace(input.workspaceId, roles);
      if (workspace.id !== "laboratory" && !roles.some((r) => ["institution_admin", "system_admin"].includes(r))) {
        throw new TRPCError({ code: "FORBIDDEN", message: "Laboratory specimens require laboratory workspace access." });
      }
      return getScopedSamples(ctx.user);
    }),
    results: protectedProcedure.input(workspaceInput).query(async ({ ctx, input }) => {
      const roles = await getUserRoles(ctx.user.id, ctx.user.role);
      selectedWorkspace(input.workspaceId, roles);
      return getScopedResults(ctx.user);
    }),
    inbox: protectedProcedure.query(({ ctx }) => getScopedInbox(ctx.user)),
    patientTimeline: protectedProcedure.query(async ({ ctx }) => {
      if (ctx.user.role !== "patient") {
        throw new TRPCError({ code: "FORBIDDEN", message: "Unified medical history is restricted to the patient's own account." });
      }
      return getPatientUnifiedTimeline(ctx.user.id, ctx.user.institutionId);
    }),
    createPatient: protectedProcedure.input(z.object({
      institutionId: z.number().int().positive().optional(),
      linkedUserId: z.number().int().positive().optional(),
      medicalRecordNumber: z.string().trim().min(1).max(64),
      nationalId: z.string().trim().max(64).optional(),
      firstName: z.string().trim().min(1).max(120),
      lastName: z.string().trim().min(1).max(120),
      dateOfBirth: z.coerce.date().optional(),
      sex: z.enum(["female", "male", "other", "unknown"]),
      phone: z.string().trim().max(32).optional(),
      email: z.string().email().max(320).optional(),
      address: z.string().trim().max(1000).optional(),
      emergencyContact: z.string().trim().max(255).optional(),
    })).mutation(({ ctx, input }) => createPatient(actorFromContext(ctx), input)),
    updatePatient: protectedProcedure.input(z.object({
      id: z.number().int().positive(),
      version: z.number().int().positive(),
      institutionId: z.number().int().positive().optional(),
      linkedUserId: z.number().int().positive().optional(),
      medicalRecordNumber: z.string().trim().min(1).max(64),
      nationalId: z.string().trim().max(64).optional(),
      firstName: z.string().trim().min(1).max(120),
      lastName: z.string().trim().min(1).max(120),
      dateOfBirth: z.coerce.date().optional(),
      sex: z.enum(["female", "male", "other", "unknown"]),
      phone: z.string().trim().max(32).optional(),
      email: z.string().email().max(320).optional(),
      address: z.string().trim().max(1000).optional(),
      emergencyContact: z.string().trim().max(255).optional(),
    })).mutation(({ ctx, input }) => updatePatient(actorFromContext(ctx), input)),
    createLabOrder: protectedProcedure.input(z.object({
      institutionId: z.number().int().positive().optional(),
      laboratoryId: z.number().int().positive(),
      patientId: z.number().int().positive(),
      orderNumber: z.string().trim().min(1).max(64),
      priority: z.enum(["routine", "urgent", "stat"]),
      clinicalNotes: z.string().trim().max(5000).optional(),
      tests: z.array(z.object({ testCode: z.string().trim().min(1).max(64), testNameAr: z.string().trim().min(1).max(255), testNameEn: z.string().trim().min(1).max(255) })).min(1).max(100),
    })).mutation(({ ctx, input }) => createLabOrder(actorFromContext(ctx), input)),
    transitionOrder: protectedProcedure.input(z.object({ id: z.number().int().positive(), version: z.number().int().positive(), nextStatus: orderStatusInput })).mutation(({ ctx, input }) => transitionOrder(actorFromContext(ctx), input)),
    registerSample: protectedProcedure.input(z.object({ orderId: z.number().int().positive(), laboratoryId: z.number().int().positive(), barcode: z.string().trim().min(1).max(128), specimenType: z.string().trim().min(1).max(100) })).mutation(({ ctx, input }) => registerSample(actorFromContext(ctx), input)),
    transitionSample: protectedProcedure.input(z.object({ id: z.number().int().positive(), version: z.number().int().positive(), nextStatus: sampleStatusInput, reason: z.string().trim().max(1000).optional() })).mutation(({ ctx, input }) => transitionSample(actorFromContext(ctx), input)),
    enterResult: protectedProcedure.input(z.object({ orderTestId: z.number().int().positive(), sampleId: z.number().int().positive(), value: z.string().trim().max(255).optional(), unit: z.string().trim().max(64).optional(), referenceRange: z.string().trim().max(255).optional(), interpretation: z.string().trim().max(3000).optional(), isCritical: z.boolean().optional() })).mutation(({ ctx, input }) => enterResult(actorFromContext(ctx), input)),
    transitionResult: protectedProcedure.input(z.object({ id: z.number().int().positive(), version: z.number().int().positive(), nextStatus: resultStatusInput, comment: z.string().trim().max(2000).optional() })).mutation(({ ctx, input }) => transitionResult(actorFromContext(ctx), input)),
    addMedicalRecord: protectedProcedure.input(z.object({ patientId: z.number().int().positive(), summary: z.string().trim().min(1).max(10000), allergies: z.string().trim().max(3000).optional(), chronicConditions: z.string().trim().max(3000).optional(), medications: z.string().trim().max(3000).optional() })).mutation(({ ctx, input }) => addMedicalRecord(actorFromContext(ctx), input)),
    workspaceCatalog: publicProcedure.query(() => workspaceCatalog),
    roleCatalog: publicProcedure.query(() => Object.entries(roleLabels).map(([id, labels]) => ({ id, ...labels }))),
    authorizationCheck: protectedProcedure.input(z.object({ workspaceId: z.string(), permission: z.string() })).query(async ({ ctx, input }) => {
      const roles = await getUserRoles(ctx.user.id, ctx.user.role);
      return { allowed: canUsePermissionInWorkspace(input.workspaceId, roles, input.permission as LisPermission), workspaceAllowed: canUseWorkspace(input.workspaceId, roles), permission: input.permission };
    }),
  }),
});

export type AppRouter = typeof appRouter;
export type LisWorkspaceId = WorkspaceId;
export type LisResultStatus = keyof typeof resultTransitions;
export type LisSampleStatus = keyof typeof sampleTransitions;
