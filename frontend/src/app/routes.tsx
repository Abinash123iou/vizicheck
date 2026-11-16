import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { PlaceholderPage } from '@/components/layout/PlaceholderPage';
import { NotFoundPage } from '@/components/layout/NotFoundPage';
import { UnauthorizedPage } from '@/components/layout/UnauthorizedPage';
import { LoginPage, getRoleLandingRoute } from '@/features/auth/LoginPage';
import { useAuthStore } from '@/stores/authStore';
import { RoleName } from '@/types/auth';

/**
 * Root index component that routes authenticated users to their role-specific home page.
 */
const RootRedirect: React.FC = () => {
  const { isAuthenticated, user, isInitializing } = useAuthStore();
  const roleName = (user?.role_name || user?.role?.name) as RoleName | undefined;

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

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (!roleName || (roleName as string) === 'VISITOR') {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Navigate to={getRoleLandingRoute(roleName)} replace />;
};

export const router = createBrowserRouter([
  // Public Route
  {
    path: '/login',
    element: <LoginPage />,
  },

  // Protected App Shell Routes
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          // Index Redirect
          {
            path: '/',
            element: <RootRedirect />,
          },

          // SUPER_ADMIN Routes
          {
            element: <ProtectedRoute allowedRoles={['SUPER_ADMIN']} />,
            children: [
              {
                path: '/tenants',
                element: (
                  <PlaceholderPage
                    title="Tenants Management"
                    moduleName="Tenants"
                    allowedRoles={['SUPER_ADMIN']}
                    description="Onboard, manage, activate, and suspend client tenant organizations."
                  />
                ),
              },
              {
                path: '/audit',
                element: (
                  <PlaceholderPage
                    title="System Audit Logs"
                    moduleName="Audit"
                    allowedRoles={['SUPER_ADMIN']}
                    description="Tamper-evident audit trail, security events, and compliance export."
                  />
                ),
              },
            ],
          },

          // SUPER_ADMIN & TENANT_ADMIN Shared Routes
          {
            element: <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'TENANT_ADMIN']} />,
            children: [
              {
                path: '/users',
                element: (
                  <PlaceholderPage
                    title="User Management"
                    moduleName="Users"
                    allowedRoles={['SUPER_ADMIN', 'TENANT_ADMIN']}
                    description="Manage platform and tenant user accounts, role bindings, and credentials."
                  />
                ),
              },
              {
                path: '/reports',
                element: (
                  <PlaceholderPage
                    title="Executive Reports"
                    moduleName="Reports"
                    allowedRoles={['SUPER_ADMIN', 'TENANT_ADMIN']}
                    description="Visitor volume analytics, peak-hour traffic, and PDF/CSV reporting."
                  />
                ),
              },
            ],
          },

          // TENANT_ADMIN & HOST_USER Shared Routes
          {
            element: <ProtectedRoute allowedRoles={['TENANT_ADMIN', 'HOST_USER']} />,
            children: [
              {
                path: '/dashboard',
                element: (
                  <PlaceholderPage
                    title="Operational Dashboard"
                    moduleName="Dashboard"
                    allowedRoles={['TENANT_ADMIN', 'HOST_USER']}
                    description="Live KPIs, upcoming visits today, and quick approval queues."
                  />
                ),
              },
              {
                path: '/approvals',
                element: (
                  <PlaceholderPage
                    title="Approval Workflows"
                    moduleName="Approvals"
                    allowedRoles={['TENANT_ADMIN', 'HOST_USER']}
                    description="Action incoming visit requests with approval, rejection, and audit reasons."
                  />
                ),
              },
              {
                path: '/availability',
                element: (
                  <PlaceholderPage
                    title="Host Availability Calendar"
                    moduleName="Availability"
                    allowedRoles={['TENANT_ADMIN', 'HOST_USER']}
                    description="Configure recurring host time slots, calendar availability, and blackout exceptions."
                  />
                ),
              },
            ],
          },

          // HOST_USER Specific Route
          {
            element: <ProtectedRoute allowedRoles={['HOST_USER']} />,
            children: [
              {
                path: '/requests',
                element: (
                  <PlaceholderPage
                    title="My Visit Requests"
                    moduleName="Requests"
                    allowedRoles={['HOST_USER']}
                    description="Track visit invitations, upcoming visitor arrivals, and pass status."
                  />
                ),
              },
            ],
          },

          // SECURITY_OFFICER Specific Routes
          {
            element: <ProtectedRoute allowedRoles={['SECURITY_OFFICER']} />,
            children: [
              {
                path: '/security/console',
                element: (
                  <PlaceholderPage
                    title="Gate Security Console"
                    moduleName="Security Operations"
                    allowedRoles={['SECURITY_OFFICER']}
                    description="Fast QR code validation, manual verification, and gate controls."
                  />
                ),
              },
              {
                path: '/checkins/active',
                element: (
                  <PlaceholderPage
                    title="Active Visitors Inside Facility"
                    moduleName="Check-In"
                    allowedRoles={['SECURITY_OFFICER']}
                    description="Live headcount roster of visitors currently on premise."
                  />
                ),
              },
              {
                path: '/checkins/scan-logs',
                element: (
                  <PlaceholderPage
                    title="Gate Scan Audit Logs"
                    moduleName="Scan Logs"
                    allowedRoles={['SECURITY_OFFICER']}
                    description="Chronological record of all barcode/QR scanner interactions."
                  />
                ),
              },
            ],
          },

          // SECURITY_OFFICER & RECEPTIONIST Shared Routes
          {
            element: <ProtectedRoute allowedRoles={['SECURITY_OFFICER', 'RECEPTIONIST']} />,
            children: [
              {
                path: '/checkins',
                element: (
                  <PlaceholderPage
                    title="Check-In & Check-Out Desk"
                    moduleName="Check-Ins"
                    allowedRoles={['SECURITY_OFFICER', 'RECEPTIONIST']}
                    description="Process physical visitor entry, check-out, and badge status changes."
                  />
                ),
              },
            ],
          },

          // RECEPTIONIST Specific Routes
          {
            element: <ProtectedRoute allowedRoles={['RECEPTIONIST']} />,
            children: [
              {
                path: '/front-desk',
                element: (
                  <PlaceholderPage
                    title="Front Desk Console"
                    moduleName="Front Desk"
                    allowedRoles={['RECEPTIONIST']}
                    description="Register walk-in visitors, create quick requests, and manage lobby queue."
                  />
                ),
              },
              {
                path: '/visitors',
                element: (
                  <PlaceholderPage
                    title="Visitor Registry"
                    moduleName="Visitors"
                    allowedRoles={['RECEPTIONIST']}
                    description="Look up visitor profiles, contact history, and identification details."
                  />
                ),
              },
              {
                path: '/passes',
                element: (
                  <PlaceholderPage
                    title="Visitor Passes"
                    moduleName="Passes"
                    allowedRoles={['RECEPTIONIST']}
                    description="Generate, print, and reissue digital and physical visitor passes."
                  />
                ),
              },
            ],
          },
        ],
      },
    ],
  },

  // 403 Forbidden Route
  {
    path: '/unauthorized',
    element: <UnauthorizedPage />,
  },

  // 404 Wildcard Route
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);

