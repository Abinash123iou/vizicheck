import React, { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Mail,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  AlertTriangle,
  Clock,
} from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useAuthStore, VALID_DASHBOARD_ROLES } from '@/stores/authStore';
import { authApi, extractApiError, ApiErrorDetail } from '@/services/api/authApi';
import { RoleName } from '@/types/auth';

// Mapping of internal roles to their default landing route
export const getRoleLandingRoute = (roleName: RoleName): string => {
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
  }
};

// Permitted route prefixes per role for safe post-login redirection
const ROLE_ALLOWED_ROUTES: Record<RoleName, string[]> = {
  SUPER_ADMIN: ['/tenants', '/users', '/audit', '/reports'],
  TENANT_ADMIN: ['/dashboard', '/approvals', '/availability', '/users', '/reports'],
  HOST_USER: ['/dashboard', '/approvals', '/availability', '/requests'],
  SECURITY_OFFICER: ['/security/console', '/checkins', '/checkins/active', '/checkins/scan-logs'],
  RECEPTIONIST: ['/front-desk', '/visitors', '/passes', '/checkins'],
};

export const isRouteAllowedForRole = (route: string, roleName: RoleName): boolean => {
  const allowed = ROLE_ALLOWED_ROUTES[roleName] || [];
  return allowed.some(
    (allowedPath) => route === allowedPath || route.startsWith(`${allowedPath}/`)
  );
};

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, isInitializing, setAuth, clearAuth } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Field validation errors
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});

  // Server error details
  const [serverError, setServerError] = useState<ApiErrorDetail | null>(null);

  // If session is restoring on page reload, render a clean loading skeleton
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

  // If already authenticated with a valid internal role, redirect to appropriate destination
  const roleName = (user?.role_name || user?.role?.name) as RoleName | undefined;
  if (isAuthenticated && user && roleName && VALID_DASHBOARD_ROLES.includes(roleName)) {
    return <Navigate to={getRoleLandingRoute(roleName)} replace />;
  }

  const validateForm = (): boolean => {
    const errors: { email?: string; password?: string } = {};

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      errors.email = 'Email address is required.';
    } else {
      // Basic email pattern validation matching standard format
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(trimmedEmail)) {
        errors.email = 'Please enter a valid email address.';
      }
    }

    if (!password) {
      errors.password = 'Password is required.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isSubmitting) return;

    setServerError(null);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const responseData = await authApi.login({
        email: email.trim(),
        password,
      });

      const authenticatedUser = responseData.user;
      const userRole = (authenticatedUser.role_name || authenticatedUser.role?.name) as
        | RoleName
        | undefined;

      // Enforce internal dashboard role requirement (reject VISITOR and unknown roles)
      if (!userRole || !VALID_DASHBOARD_ROLES.includes(userRole)) {
        clearAuth();
        setServerError({
          message:
            'Access denied. Visitor accounts and unauthorized roles cannot access the internal administration console.',
          status: 403,
        });
        setIsSubmitting(false);
        return;
      }

      // Store in Zustand memory + sessionStorage
      setAuth(authenticatedUser, responseData.access_token, responseData.refresh_token);

      // Determine post-login redirect path
      const stateFrom = (location.state as { from?: { pathname?: string } })?.from?.pathname;
      let targetRoute = getRoleLandingRoute(userRole);

      if (
        stateFrom &&
        typeof stateFrom === 'string' &&
        stateFrom.startsWith('/') &&
        !stateFrom.startsWith('//') &&
        stateFrom !== '/login' &&
        stateFrom !== '/unauthorized'
      ) {
        if (isRouteAllowedForRole(stateFrom, userRole)) {
          targetRoute = stateFrom;
        }
      }

      navigate(targetRoute, { replace: true });
    } catch (err) {
      const errorDetail = extractApiError(err);
      setServerError(errorDetail);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center bg-[#F8FAFC] px-4 py-8 sm:px-6 lg:px-8">
      {/* Brand Icon & Heading */}
      <div className="w-full max-w-md text-center mb-6">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[#2563EB] text-white shadow-md shadow-blue-500/20 mb-3">
          <ShieldCheck className="w-7 h-7" aria-hidden="true" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">ViziCheck</h1>
        <p className="text-xs text-slate-500 font-medium mt-1">
          Enterprise Smart Visitor Management System
        </p>
      </div>

      {/* Main Login Card */}
      <div className="w-full max-w-md bg-white rounded-xl border border-[#E2E8F0] p-6 sm:p-8 shadow-xs">
        <div className="mb-6">
          <h2 className="text-base font-semibold text-slate-900">Sign in to your account</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Enter your workplace credentials to access the console.
          </p>
        </div>

        {/* Server Error Alert Banner */}
        {serverError && (
          <div
            role="alert"
            className={`mb-5 p-3.5 rounded-lg border text-xs ${
              serverError.isLocked
                ? 'bg-amber-50 border-amber-200 text-amber-900'
                : serverError.status === 403
                ? 'bg-orange-50 border-orange-200 text-orange-900'
                : 'bg-red-50 border-red-200 text-red-900'
            }`}
          >
            <div className="flex items-start gap-2.5">
              {serverError.isLocked ? (
                <Clock className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" aria-hidden="true" />
              ) : serverError.status === 403 ? (
                <AlertTriangle
                  className="w-4 h-4 text-orange-600 shrink-0 mt-0.5"
                  aria-hidden="true"
                />
              ) : (
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" aria-hidden="true" />
              )}
              <div className="flex-1 space-y-1">
                <p className="font-semibold">{serverError.message}</p>
                {serverError.lockedUntil && (
                  <p className="text-[11px] text-amber-800">
                    Lockout expires at: <span className="font-mono font-bold">{serverError.lockedUntil}</span>
                  </p>
                )}
                {serverError.errors && serverError.errors.length > 0 && (
                  <ul className="list-disc list-inside mt-1 space-y-0.5 text-[11px] text-red-800">
                    {serverError.errors.map((errItem, idx) => (
                      <li key={idx}>{errItem}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          <Input
            label="Work Email"
            type="email"
            id="email"
            autoComplete="email"
            autoFocus
            required
            placeholder="admin@vizicheck.com"
            value={email}
            disabled={isSubmitting}
            error={fieldErrors.email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (fieldErrors.email) {
                setFieldErrors((prev) => ({ ...prev, email: undefined }));
              }
            }}
            leadingIcon={<Mail className="w-4 h-4" />}
          />

          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            id="password"
            autoComplete="current-password"
            required
            placeholder="••••••••••••"
            value={password}
            disabled={isSubmitting}
            error={fieldErrors.password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (fieldErrors.password) {
                setFieldErrors((prev) => ({ ...prev, password: undefined }));
              }
            }}
            leadingIcon={<Lock className="w-4 h-4" />}
            trailingAction={
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="p-1 text-slate-400 hover:text-slate-600 focus:outline-none focus:text-slate-600"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            }
          />

          <div className="pt-2">
            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isSubmitting}
              className="w-full justify-center shadow-xs text-sm font-semibold"
            >
              {isSubmitting ? 'Signing in...' : 'Sign In'}
            </Button>
          </div>
        </form>
      </div>

      {/* Enterprise Security Footer */}
      <div className="w-full max-w-md mt-6 text-center text-[11px] text-slate-400">
        <p>Secured with TLS encryption & Role-Based Access Control.</p>
        <p className="mt-0.5">ViziCheck &copy; 2026. All rights reserved.</p>
      </div>
    </div>
  );
};

