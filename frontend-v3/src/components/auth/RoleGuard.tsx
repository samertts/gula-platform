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
  const { user, demoMode } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (demoMode && !roles.includes(user.role as UserRole)) {
    return <Navigate to={fallback} replace />;
  }

  return <>{children}</>;
}