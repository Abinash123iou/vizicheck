import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldCheck,
  Building2,
  Users,
  ShieldAlert,
  BarChart3,
  LayoutDashboard,
  CheckSquare,
  Calendar,
  ClipboardList,
  ScanLine,
  UserCheck,
  FileText,
  CreditCard,
  ChevronLeft,
  ChevronRight,
  X,
  type LucideIcon,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { RoleName } from '@/types/auth';
import { cn } from '@/utils/cn';

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

// Verified Navigation matrix mapped strictly to the 5 internal roles
const ROLE_NAVIGATION: Record<RoleName, NavItem[]> = {
  SUPER_ADMIN: [
    { label: 'Tenants', href: '/tenants', icon: Building2 },
    { label: 'Users', href: '/users', icon: Users },
    { label: 'Audit Logs', href: '/audit', icon: ShieldAlert },
    { label: 'Reports', href: '/reports', icon: BarChart3 },
  ],
  TENANT_ADMIN: [
    { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { label: 'Approvals', href: '/approvals', icon: CheckSquare },
    { label: 'Users', href: '/users', icon: Users },
    { label: 'Availability', href: '/availability', icon: Calendar },
    { label: 'Reports', href: '/reports', icon: BarChart3 },
  ],
  HOST_USER: [
    { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { label: 'My Requests', href: '/requests', icon: ClipboardList },
    { label: 'Availability Calendar', href: '/availability', icon: Calendar },
    { label: 'Approvals', href: '/approvals', icon: CheckSquare },
  ],
  SECURITY_OFFICER: [
    { label: 'Gate Console', href: '/security/console', icon: ScanLine },
    { label: 'Check-Ins', href: '/checkins', icon: UserCheck },
    { label: 'Active Visitors', href: '/checkins/active', icon: Users },
    { label: 'Scan Logs', href: '/checkins/scan-logs', icon: FileText },
  ],
  RECEPTIONIST: [
    { label: 'Front Desk', href: '/front-desk', icon: LayoutDashboard },
    { label: 'Visitors', href: '/visitors', icon: Users },
    { label: 'Passes', href: '/passes', icon: CreditCard },
    { label: 'Check-Ins', href: '/checkins', icon: UserCheck },
  ],
};

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  onToggleCollapse,
  isMobileOpen,
  onCloseMobile,
}) => {
  const { user } = useAuthStore();
  const roleName = (user?.role_name || user?.role?.name) as RoleName | undefined;

  const navItems = roleName && ROLE_NAVIGATION[roleName] ? ROLE_NAVIGATION[roleName] : [];

  return (
    <>
      {/* Mobile Drawer Overlay */}
      {isMobileOpen && (
        <div
          role="presentation"
          aria-hidden="true"
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-xs transition-opacity lg:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        aria-label="Sidebar Navigation"
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex flex-col bg-[#0F172A] border-r border-[#1E293B] text-white transition-all duration-200 ease-in-out',
          // Desktop sizing
          'lg:static lg:z-auto',
          isCollapsed ? 'lg:w-20' : 'lg:w-64',
          // Mobile responsive drawer handling
          isMobileOpen ? 'translate-x-0 w-64' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-[#1E293B]">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-9 h-9 rounded-md bg-[#2563EB] flex items-center justify-center text-white shrink-0 shadow-xs">
              <ShieldCheck className="w-5 h-5" aria-hidden="true" />
            </div>
            {(!isCollapsed || isMobileOpen) && (
              <div className="flex items-center gap-2 overflow-hidden">
                <span className="text-base font-bold tracking-tight text-white truncate">ViziCheck</span>
                <span className="text-[10px] font-medium uppercase tracking-wider text-slate-300 bg-[#1E293B] px-1.5 py-0.5 rounded border border-slate-700/60 shrink-0">
                  Enterprise
                </span>
              </div>
            )}
          </div>

          {/* Close button on mobile */}
          <button
            type="button"
            onClick={onCloseMobile}
            className="lg:hidden p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#2563EB]"
            aria-label="Close navigation sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav aria-label="Main Navigation" className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.href}
                to={item.href}
                onClick={() => {
                  if (isMobileOpen) onCloseMobile();
                }}
                className={({ isActive }) =>
                  cn(
                    'group flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors select-none focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2 focus:ring-offset-[#0F172A]',
                    isActive
                      ? 'bg-[#2563EB] text-white shadow-xs font-semibold'
                      : 'text-[#94A3B8] hover:bg-[#1E293B] hover:text-white',
                    isCollapsed && !isMobileOpen && 'justify-center px-2'
                  )
                }
                title={isCollapsed && !isMobileOpen ? item.label : undefined}
                aria-label={item.label}
              >
                <Icon className="w-5 h-5 shrink-0" aria-hidden="true" />
                {(!isCollapsed || isMobileOpen) && <span className="truncate">{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>

        {/* Desktop Collapse Toggle Footer */}
        <div className="hidden lg:flex items-center justify-between p-3 border-t border-[#1E293B]">
          {!isCollapsed && (
            <span className="text-xs text-slate-400 truncate pl-2 font-medium">
              Collapse Sidebar
            </span>
          )}
          <button
            type="button"
            onClick={onToggleCollapse}
            className={cn(
              'p-2 rounded-md text-slate-400 hover:text-white hover:bg-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#2563EB]',
              isCollapsed && 'w-full flex justify-center'
            )}
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
          </button>
        </div>
      </aside>
    </>
  );
};

