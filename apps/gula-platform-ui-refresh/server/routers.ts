import { COOKIE_NAME } from "@shared/const";
import { z } from "zod";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { getGulaConnectionStatus, verifyGulaAuthorizationContext } from "./gula/backendClient";
import { readScopedOrders, readScopedPatients } from "./gula/scopedReads";
import { resolveVerifiedWorkspaceContext } from "./gula/workspaceContext";
import { adminProcedure, protectedProcedure, publicProcedure, router } from "./_core/trpc";

const listInput = z.object({
  skip: z.number().int().min(0).default(0),
  limit: z.number().int().min(1).max(50).default(25),
});

export const appRouter = router({
    // if you need to use socket.io, read and register route in server/_core/index.ts, all api should start with '/api/' so that the gateway can route correctly
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),
  integration: router({
    connectionStatus: publicProcedure.query(() => getGulaConnectionStatus()),
    verifyAuthorizationContext: adminProcedure.query(() => verifyGulaAuthorizationContext()),
  }),
  workspace: router({
    status: protectedProcedure.query(async ({ ctx }) => {
      const workspace = await resolveVerifiedWorkspaceContext(ctx.user.id);
      if (workspace.state === "workspace_unavailable") return workspace;
      return {
        state: workspace.state,
        label: "سياق المنشأة موثق",
        description: "يوجد ربط خادمي نشط. لا تُعرض معرفات المختبر أو المنشأة للمتصفح من هذا الإجراء.",
      } as const;
    }),
  }),
  patients: router({
    list: protectedProcedure.input(listInput.extend({ search: z.string().trim().max(100).optional() })).query(async ({ ctx, input }) => {
      const workspace = await resolveVerifiedWorkspaceContext(ctx.user.id);
      if (workspace.state === "workspace_unavailable") {
        return { ...workspace, contractId: "patients.read", requiredPermission: "patients:read" } as const;
      }
      return readScopedPatients(workspace.context, input);
    }),
  }),
  orders: router({
    list: protectedProcedure.input(listInput.extend({ status: z.string().trim().max(80).optional() })).query(async ({ ctx, input }) => {
      const workspace = await resolveVerifiedWorkspaceContext(ctx.user.id);
      if (workspace.state === "workspace_unavailable") {
        return { ...workspace, contractId: "orders.read", requiredPermission: "orders:read" } as const;
      }
      return readScopedOrders(workspace.context, input);
    }),
  }),

  // TODO: add feature routers here, e.g.
  // todo: router({
  //   list: protectedProcedure.query(({ ctx }) =>
  //     db.getUserTodos(ctx.user.id)
  //   ),
  // }),
});

export type AppRouter = typeof appRouter;
