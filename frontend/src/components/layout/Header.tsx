import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, Globe, Building, LogOut, ChevronDown } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { RoleName } from '@/types/auth';

interface HeaderProps {
  onOpenMobileSidebar: () => void;
}

// Map route paths to readable titles
const ROUTE_TITLES: Record<string, string> = {
  '/tenants': 'Tenant Management',
  '/users': 'User Directory',
  '/audit': 'System Audit Logs',
  '/reports': 'Executive Reports & Analytics',
  '/dashboard': 'Operational Dashboard',
  '/approvals': 'Approval Workflows',
  '/availability': 'Host Availability Management',
  '/requests': 'Visit Requests',
  '/security/console': 'Security Operations Console',
  '/checkins': 'Gate Check-In & Check-Out',
  '/checkins/active': 'Active Visitors Roster',
  '/checkins/scan-logs': 'Gate Scan Audit Logs',
  '/front-desk': 'Front Desk Console',
  '/visitors': 'Visitor Registry',
  '/passes': 'Visitor Passes',
};

export const Header: React.FC<HeaderProps> = ({ onOpenMobileSidebar }) => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const roleName = (user?.role_name || user?.role?.name) as RoleName | undefined;
  const isSuperAdmin = roleName === 'SUPER_ADMIN';

  // Format tenant context label
  const tenantContextLabel = isSuperAdmin
    ? 'Platform Administration'
    : user?.tenant_name || (user?.tenant_id ? `Tenant #${user.tenant_id}` : 'General Facility');

  // Derive current page title from path
  const currentTitle = ROUTE_TITLES[location.pathname] || 'Administration';

  const userDisplayName = user
    ? `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email
    : 'User';

  const userInitials = user
    ? `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase() || 'U'
    : 'U';

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <header className="h-16 bg-[#0F172A] border-b border-[#1E293B] text-white flex items-center justify-between px-4 sm:px-6 z-30 shrink-0">
      {/* Left Area: Mobile Toggle & Page Title */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenMobileSidebar}
          className="lg:hidden p-2 rounded-md text-slate-300 hover:text-white hover:bg-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#2563EB]"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white tracking-tight sm:text-base">
            {currentTitle}
          </span>
        </div>
      </div>

      {/* Right Area: Tenant Context & User Dropdown */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Tenant Context Pill */}
        <div
          className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-[#1E293B] text-slate-300 border border-slate-700/60 max-w-[220px] truncate"
          title={tenantContextLabel}
        >
          {isSuperAdmin ? (
            <Globe className="w-3.5 h-3.5 text-[#2563EB] shrink-0" aria-hidden="true" />
          ) : (
            <Building className="w-3.5 h-3.5 text-slate-400 shrink-0" aria-hidden="true" />
          )}
          <span className="truncate">{tenantContextLabel}</span>
        </div>

        {/* User Profile Menu */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setDropdownOpen((prev) => !prev)}
            aria-expanded={dropdownOpen}
            aria-haspopup="true"
            className="flex items-center gap-2.5 p-1.5 rounded-md hover:bg-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#2563EB] transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-[#1E293B] border border-slate-700 flex items-center justify-center text-xs font-bold text-white shrink-0">
              {userInitials}
            </div>
            <div className="hidden md:flex flex-col text-left">
              <span className="text-xs font-semibold text-white leading-tight max-w-[130px] truncate">
                {userDisplayName}
              </span>
              <span className="text-[10px] text-slate-400 font-medium leading-tight uppercase tracking-wider">
                {roleName || 'Guest'}
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden md:block" aria-hidden="true" />
          </button>

          {/* Dropdown Popover */}
          {dropdownOpen && (
            <div
              role="menu"
              className="absolute right-0 mt-2 w-64 rounded-md bg-[#0F172A] border border-[#1E293B] shadow-lg py-1.5 z-50 text-slate-200"
            >
              {/* User Summary Info */}
              <div className="px-4 py-2.5 border-b border-[#1E293B]">
                <p className="text-xs font-semibold text-white truncate">{userDisplayName}</p>
                <p className="text-[11px] text-slate-400 truncate mt-0.5">{user?.email || 'No email'}</p>
                <div className="mt-2 flex items-center gap-1.5">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-[#1E293B] text-blue-400 border border-slate-700 uppercase tracking-wider">
                    {roleName || 'UNKNOWN'}
                  </span>
                  {!isSuperAdmin && user?.tenant_name && (
                    <span className="text-[10px] text-slate-400 truncate">
                      • {user.tenant_name}
                    </span>
                  )}
                </div>
              </div>

              {/* Mobile Tenant Pill Display */}
              <div className="sm:hidden px-4 py-2 border-b border-[#1E293B] text-xs text-slate-300 flex items-center gap-2">
                {isSuperAdmin ? (
                  <Globe className="w-3.5 h-3.5 text-[#2563EB]" />
                ) : (
                  <Building className="w-3.5 h-3.5 text-slate-400" />
                )}
                <span className="truncate">{tenantContextLabel}</span>
              </div>

              {/* Actions */}
              <div className="py-1">
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-4 py-2 text-xs font-medium text-red-400 hover:bg-[#1E293B] hover:text-red-300 text-left transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
