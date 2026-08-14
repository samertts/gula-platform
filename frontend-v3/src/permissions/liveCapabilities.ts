export type ReflectedPermissions = Record<string, string[]>;

/**
 * Live capabilities are only a server-reflected UX hint. An empty or missing
 * reflection is deliberately denied here; backend authorization remains the
 * final enforcement boundary.
 */
export function hasReflectedPermission(
  effectivePermissions: ReflectedPermissions,
  requiredPermissions: string[],
): boolean {
  if (requiredPermissions.length === 0) return true;
  const reflected = new Set(Object.values(effectivePermissions).flat());
  return requiredPermissions.some((permission) => reflected.has(permission));
}
