import React, { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import {
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
import vizicheckLogo from '@/assets/vizicheck-logo.png';
import authIllustration from '@/assets/auth-illustration.png';

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
  const [rememberMe, setRememberMe] = useState(false);
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
    <div className="min-h-screen w-full bg-[#F8FAFC] flex items-center justify-center p-3 sm:p-6 lg:p-8 font-sans">
      {/* Outer Card Container */}
      <div className="w-full max-w-5xl bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-200/80 overflow-hidden grid grid-cols-1 lg:grid-cols-12 min-h-[640px]">

        {/* Left Column: Focused Authentication Form */}
        <div className="lg:col-span-6 xl:col-span-5 flex flex-col justify-between p-6 sm:p-10 lg:p-12 bg-white">
          <div>
            {/* Brand Logo & Name */}
            <div className="flex items-center gap-3 mb-8 sm:mb-10">
              <img
                src={vizicheckLogo}
                alt="ViziCheck Logo"
                className="w-10 h-10 object-contain drop-shadow-sm"
              />
              <div className="flex flex-col">
                <span className="text-lg font-bold text-slate-900 tracking-tight leading-tight">ViziCheck</span>
                <span className="text-[10px] font-semibold text-blue-600 uppercase tracking-wider">Enterprise Console</span>
              </div>
            </div>

            {/* Heading */}
            <div className="mb-6">
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Sign in</h1>
              <p className="text-xs sm:text-sm text-slate-500 mt-1">
                Enter your workplace credentials to access the console.
              </p>
            </div>

            {/* Server Error Alert Banner */}
            {serverError && (
              <div
                role="alert"
                className={`mb-5 p-3.5 rounded-xl border text-xs ${serverError.isLocked
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
                        Lockout expires at:{' '}
                        <span className="font-mono font-bold">{serverError.lockedUntil}</span>
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

            {/* Form */}
            <form onSubmit={handleSubmit} noValidate className="space-y-4">
              <Input
                label="Email Address"
                type="email"
                id="email"
                autoComplete="email"
                autoFocus
                required
                placeholder="johndoe@gmail.com"
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
                className="rounded-xl border-slate-200 py-2.5 shadow-2xs"
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
                className="rounded-xl border-slate-200 py-2.5 shadow-2xs"
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

              {/* Remember Me */}
              <div className="flex items-center justify-between pt-0.5 text-xs">
                <label className="flex items-center gap-2 cursor-pointer select-none text-slate-600">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-300 text-[#2563EB] focus:ring-[#2563EB] transition-colors"
                  />
                  <span>Remember me</span>
                </label>
              </div>

              {/* Sign In Button */}
              <div className="pt-2">
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  isLoading={isSubmitting}
                  className="w-full justify-center rounded-xl bg-[#2563EB] hover:bg-[#1D4ED8] focus:ring-4 focus:ring-[#2563EB]/20 text-white py-3 shadow-md shadow-blue-600/25 active:scale-[0.99] transition-all font-semibold text-sm"
                >
                  {isSubmitting ? 'Signing in...' : 'Sign in'}
                </Button>
              </div>
            </form>
          </div>

          {/* Footer Security Badge */}
          <div className="mt-8 pt-4 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
            <span>TLS 1.3 Encryption & RBAC</span>
            <span>ViziCheck &copy; 2026</span>
          </div>
        </div>

        {/* Right Column: Brand Blue Hero Showcase Panel with Office Illustration */}
        <div className="hidden lg:flex lg:col-span-6 xl:col-span-7 bg-gradient-to-br from-[#1D4ED8] via-[#2563EB] to-[#1E40AF] p-8 lg:p-10 relative overflow-hidden flex-col justify-between text-white rounded-2xl m-3 border border-blue-400/30 shadow-xl">
          {/* Subtle Ambient Beam Background */}
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-white/20 via-blue-200/10 to-transparent pointer-events-none rotate-12 transform origin-top-right" />
          <div className="absolute -bottom-10 -left-10 w-72 h-72 bg-white/10 rounded-full blur-3xl pointer-events-none" />

          {/* Top Tagline */}
          <div className="relative z-10">
            <span className="text-xs sm:text-sm font-bold tracking-wider uppercase text-white">
              ViziCheck Enterprise Suite
            </span>
          </div>

          {/* Center Showcase with Team Illustration */}
          <div className="relative z-10 my-auto flex flex-col items-center text-center py-6">
            {/* Illustrated Office Card */}
            <div className="w-full max-w-sm sm:max-w-md bg-white rounded-2xl p-5 sm:p-6 shadow-2xl border border-white/40 mb-6 transform hover:scale-[1.01] transition-transform">
              <img
                src={authIllustration}
                alt="Smart Workplace Visitor Management"
                className="w-full h-auto max-h-56 sm:max-h-64 object-contain mx-auto"
              />
            </div>

            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight">
              Welcome to ViziCheck
            </h2>
            <p className="text-xs sm:text-sm text-white font-semibold mt-2.5 max-w-md leading-relaxed">
              Empower your lobby reception, hosts, and security teams with unified check-ins, real-time approval queues, and gate security.
            </p>
            <p className="text-xs sm:text-sm text-blue-100 mt-2 font-bold">
              Over 50k+ visitors verified across multi-tenant corporate campuses.
            </p>
          </div>

          {/* Bottom Security Standards Note */}
          <div className="relative z-10 flex items-center justify-between text-[11px] sm:text-xs text-white font-bold pt-4 border-t border-white/20">
            <span>Enterprise Multi-Tenant Security</span>
            <span>Real-Time Gate Verification</span>
          </div>

        </div>

      </div>
    </div>
  );
};
