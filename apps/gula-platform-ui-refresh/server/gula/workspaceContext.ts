import { getActiveGulaWorkspaceBinding } from "../db";

export type VerifiedWorkspaceContext = {
  gulaSubjectId: number;
  labId: number;
  organizationId: number | null;
  facilityId: number | null;
  assignmentRoleId: string | null;
  verifiedAt: Date;
};

export type WorkspaceContextResolution =
  | { state: "workspace_unavailable"; label: string; description: string }
  | { state: "workspace_ready"; context: VerifiedWorkspaceContext };

/**
 * Resolves only a previously recorded, active binding. This deliberately does
 * not infer a tenant from a local role or accept a browser-provided lab id.
 */
export async function resolveVerifiedWorkspaceContext(userId: number): Promise<WorkspaceContextResolution> {
  const binding = await getActiveGulaWorkspaceBinding(userId);
  if (!binding) {
    return {
      state: "workspace_unavailable",
      label: "سياق المنشأة غير موثق",
      description: "لا يوجد ربط خادمي نشط يثبت المختبر والتعيين للمستخدم الحالي؛ لذلك لن يُنفذ أي طلب مرضى أو طلبات.",
    };
  }

  return {
    state: "workspace_ready",
    context: {
      gulaSubjectId: binding.gulaSubjectId,
      labId: binding.labId,
      organizationId: binding.organizationId,
      facilityId: binding.facilityId,
      assignmentRoleId: binding.assignmentRoleId,
      verifiedAt: binding.verifiedAt,
    },
  };
}
