import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldX, LogOut, Home } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/stores/authStore';

export const UnauthorizedPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const roleName = user?.role_name || user?.role?.name;

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC] p-4">
      <div className="max-w-md w-full bg-white rounded-lg border border-slate-200 p-8 text-center shadow-xs">
        <div className="w-14 h-14 rounded-full bg-red-50 text-[#DC2626] flex items-center justify-center mx-auto mb-4 border border-red-100">
          <ShieldX className="w-7 h-7" />
        </div>
        <span className="text-xs font-bold uppercase tracking-wider text-red-500">Access Denied (403)</span>
        <h1 className="text-xl font-bold text-slate-900 mt-1">Unauthorized Access</h1>
        <p className="text-sm text-slate-500 mt-2">
          Your current account role ({roleName || 'None'}) does not have permission to access this internal dashboard section.
        </p>

        <div className="mt-6 flex flex-col sm:flex-row items-center gap-3">
          <Button
            variant="outline"
            onClick={() => {
              logout();
              navigate('/login', { replace: true });
            }}
            className="w-full gap-2 text-xs"
          >
            <LogOut className="w-4 h-4 text-red-500" />
            <span>Switch Account</span>
          </Button>

          <Button
            variant="primary"
            onClick={() => navigate('/', { replace: true })}
            className="w-full gap-2 text-xs"
          >
            <Home className="w-4 h-4" />
            <span>Go to Allowed Area</span>
          </Button>
        </div>
      </div>
    </div>
  );
};

