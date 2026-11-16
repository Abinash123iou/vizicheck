import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { RoleName } from '@/types/auth';

const VALID_DASHBOARD_ROLES: RoleName[] = [
  'SUPER_ADMIN',
  'TENANT_ADMIN',
  'HOST_USER',
  'SECURITY_OFFICER',
  'RECEPTIONIST',
];

interface ProtectedRouteProps {
  allowedRoles?: RoleName[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ allowedRoles }) => {
  const { isAuthenticated, user, isInitializing, hasRole } = useAuthStore();
  const location = useLocation();

  // 1. Session restoration in-flight check
  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-[#2563EB] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-medium text-slate-500">Restoring session...</span>
        </div>
      </div>
    );
  }

  // 2. Unauthenticated check
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const userRole = (user.role_name || user.role?.name) as RoleName | undefined;

  // 2. Reject external or non-dashboard roles (e.g. VISITOR)
  if (!userRole || !VALID_DASHBOARD_ROLES.includes(userRole)) {
    return <Navigate to="/unauthorized" replace />;
  }

  // 3. Specific role authorization check
  if (allowedRoles && allowedRoles.length > 0 && !hasRole(allowedRoles)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
};
