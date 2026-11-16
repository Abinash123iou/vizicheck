import { create } from 'zustand';
import { User, RoleName } from '@/types/auth';
import { tokenStorage } from '@/services/api/tokenStorage';
import { queryClient } from '@/config/queryClient';
import { authApi } from '@/services/api/authApi';
import { apiClient } from '@/services/api/client';

export const VALID_DASHBOARD_ROLES: RoleName[] = [
  'SUPER_ADMIN',
  'TENANT_ADMIN',
  'HOST_USER',
  'SECURITY_OFFICER',
  'RECEPTIONIST',
];

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  updateAccessToken: (accessToken: string) => void;
  clearAuth: () => void;
  logout: () => Promise<void>;
  hasRole: (roles: RoleName[]) => boolean;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => {
  // Listen for global logout events triggered by axios interceptor or window events
  if (typeof window !== 'undefined') {
    window.addEventListener('auth:logout', () => {
      get().clearAuth();
    });
  }

  return {
    user: null,
    accessToken: null,
    isAuthenticated: false,
    isInitializing: true,

    setAuth: (user, accessToken, refreshToken) => {
      // Refresh token stored ONLY in sessionStorage
      tokenStorage.setRefreshToken(refreshToken);

      // Access token attached to client headers
      apiClient.defaults.headers.common.Authorization = `Bearer ${accessToken}`;

      set({
        user,
        accessToken,
        isAuthenticated: true,
        isInitializing: false,
      });
    },

    updateAccessToken: (accessToken) => {
      apiClient.defaults.headers.common.Authorization = `Bearer ${accessToken}`;
      set({ accessToken });
    },

    clearAuth: () => {
      tokenStorage.clearRefreshToken();
      delete apiClient.defaults.headers.common.Authorization;

      try {
        queryClient.clear();
      } catch {
        // QueryClient cleanup if initialized
      }

      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isInitializing: false,
      });
    },

    logout: async () => {
      try {
        await authApi.logout();
      } finally {
        get().clearAuth();
      }
    },

    hasRole: (roles) => {
      const currentUser = get().user;
      const roleName = (currentUser?.role_name || currentUser?.role?.name) as RoleName | undefined;
      if (!roleName) return false;
      return roles.includes(roleName);
    },

    initialize: async () => {
      const refreshToken = tokenStorage.getRefreshToken();

      if (!refreshToken) {
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
          isInitializing: false,
        });
        return;
      }

      try {
        // 1. Exchange existing session refresh token for a fresh rotated pair
        const tokenData = await authApi.refresh(refreshToken);

        // 2. Query user profile using newly minted access token
        const profile = await authApi.getMeWithToken(tokenData.access_token);

        // 3. Verify user has an authorized internal dashboard role
        const roleName = (profile.role_name || profile.role?.name) as RoleName | undefined;
        if (!roleName || !VALID_DASHBOARD_ROLES.includes(roleName)) {
          get().clearAuth();
          return;
        }

        // 4. Update in-memory auth state
        apiClient.defaults.headers.common.Authorization = `Bearer ${tokenData.access_token}`;
        set({
          user: profile,
          accessToken: tokenData.access_token,
          isAuthenticated: true,
          isInitializing: false,
        });
      } catch {
        // If refresh or profile validation fails, clear stale session
        get().clearAuth();
      }
    },
  };
});
