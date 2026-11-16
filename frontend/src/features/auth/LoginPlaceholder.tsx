import React from 'react';
import { Navigate } from 'react-router-dom';
import { ShieldCheck, Lock } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { RoleName } from '@/types/auth';

export const getRoleLandingRoute = (roleName?: RoleName): string => {
  switch (roleName) {
    case 'SUPER_ADMIN':
      return '/tenants';
    case 'TENANT_ADMIN':
      return '/dashboard';
    case 'HOST_USER':
      return '/requests';
    case 'SECURITY_OFFICER':
      return '/security/console';
    case 'RECEPTIONIST':
      return '/front-desk';
    default:
      return '/unauthorized';
  }
};

export const LoginPlaceholder: React.FC = () => {
  const { isAuthenticated, user } = useAuthStore();
  const roleName = (user?.role_name || user?.role?.name) as RoleName | undefined;

  // If already authenticated with a valid internal dashboard role, redirect to role home
  if (isAuthenticated && user && roleName && roleName !== ('VISITOR' as unknown as RoleName)) {
    return <Navigate to={getRoleLandingRoute(roleName)} replace />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC] p-4">
      <div className="max-w-md w-full bg-white rounded-lg border border-slate-200 p-8 shadow-xs text-center">
        <div className="w-12 h-12 rounded-md bg-[#2563EB] text-white flex items-center justify-center mx-auto mb-4 shadow-xs">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <h1 className="text-xl font-bold text-slate-900">ViziCheck Login</h1>
        <p className="text-sm text-slate-500 mt-1">
          Stage 5 Authentication & API integration point.
        </p>

        <div className="mt-6 p-4 rounded-md bg-blue-50 border border-blue-100 text-left text-xs text-slate-700 space-y-2">
          <div className="flex items-center gap-2 font-semibold text-blue-900">
            <Lock className="w-4 h-4 text-[#2563EB]" />
            <span>Stage 4 Routing Active</span>
          </div>
          <p className="text-slate-600">
            The full enterprise login screen, credential validation, lockout handling, and FastAPI JWT exchange will be implemented in Stage 5.
          </p>
        </div>
      </div>
    </div>
  );
};

