import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import type { UserRole } from "@/types";
import type { ReactNode } from "react";

interface RoleGuardProps {
  children: ReactNode;
  roles: UserRole[];
  fallback?: string;
}

export function RoleGuard({ children, roles, fallback = "/dashboard" }: RoleGuardProps) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // The role check applies to every authenticated user, not only to demo
  // personas. Guarding it on `demoMode` meant that outside a demo session every
  // signed-in user passed every RoleGuard, so the route policy was inert in the
  // only mode that matters.
  //
  // This is navigation, not authorization. It keeps a user out of a route their
  // role cannot use; it grants nothing. The server remains the sole authority
  // on identity, membership, workspace eligibility, role and permission, and
  // still refuses the data behind any route reached another way.
  if (!roles.includes(user.role as UserRole)) {
    return <Navigate to={fallback} replace />;
  }

  return <>{children}</>;
}