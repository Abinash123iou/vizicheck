import axios from 'axios';
import { apiClient } from './client';
import { tokenStorage } from './tokenStorage';
import { ApiResponse } from '@/types/api';
import {
  LoginRequest,
  LoginResponseData,
  TokenResponseData,
  User,
} from '@/types/auth';

export interface ApiErrorDetail {
  message: string;
  status?: number;
  errors?: string[];
  isLocked?: boolean;
  lockedUntil?: string;
}

/**
 * Safely extracts human-readable error details from backend error responses.
 * Never exposes stack traces or sensitive internals.
 */
export const extractApiError = (error: unknown): ApiErrorDetail => {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const data = error.response?.data as ApiResponse<unknown> | undefined;

    // Default message when backend is unreachable or CORS blocked
    let message = data?.message;
    if (!message) {
      if (!error.response || status === 0) {
        message = 'Unable to connect to authentication server. Please ensure the backend is running.';
      } else if (status === 401) {
        message = 'Invalid email address or password.';
      } else if (status === 403) {
        message = 'Access denied. Your account or organization is inactive.';
      } else if (status === 422) {
        message = 'Validation failed. Please verify your submitted credentials.';
      } else if (status === 423) {
        message = 'Account is temporarily locked due to multiple failed login attempts.';
      } else {
        message = error.message || 'Authentication request failed.';
      }
    }

    // Check for lockout pattern: status 423 or message mentioning locked
    const isLocked =
      status === 423 ||
      (typeof message === 'string' && message.toLowerCase().includes('temporarily locked'));

    // Extract exact lockout expiry timestamp if backend provided one e.g. "until 14:30:00 UTC"
    let lockedUntil: string | undefined;
    if (isLocked && typeof message === 'string') {
      const match = message.match(/until\s+([0-9:]+(\s*[A-Za-z]+)?)/i);
      if (match) {
        lockedUntil = match[1];
      }
    }

    const errors = data?.errors
      ? Array.isArray(data.errors)
        ? data.errors.map(String)
        : [String(data.errors)]
      : [];

    return {
      message,
      status,
      errors,
      isLocked,
      lockedUntil,
    };
  }

  return {
    message: error instanceof Error ? error.message : 'An unexpected error occurred.',
    errors: [],
  };
};

export const authApi = {
  /**
   * Authenticate user with credentials and retrieve access token, refresh token, and user profile.
   */
  async login(credentials: LoginRequest): Promise<LoginResponseData> {
    const response = await apiClient.post<ApiResponse<LoginResponseData>>(
      '/auth/login',
      credentials
    );

    if (!response.data.success || !response.data.data) {
      throw new Error(response.data.message || 'Login failed');
    }

    return response.data.data;
  },

  /**
   * Rotate access and refresh token pair using an existing refresh token.
   * Stores the newly rotated refresh token into sessionStorage immediately.
   */
  async refresh(refreshToken: string): Promise<TokenResponseData> {
    const response = await apiClient.post<ApiResponse<TokenResponseData>>(
      '/auth/refresh',
      { refresh_token: refreshToken }
    );

    if (!response.data.success || !response.data.data) {
      throw new Error(response.data.message || 'Failed to refresh authentication session');
    }

    const data = response.data.data;
    if (data.refresh_token) {
      tokenStorage.setRefreshToken(data.refresh_token);
    }

    return data;
  },

  /**
   * Log out user from backend session audit log.
   * Note: The backend records an audit log; it does not maintain a server-side JWT blocklist.
   * Frontend will unconditionally discard tokens locally.
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post<ApiResponse<unknown>>('/auth/logout');
    } catch {
      // Ignore network or 401 errors during logout; local session is always destroyed
    }
  },

  /**
   * Fetch current authenticated user's profile and permissions using active access token.
   */
  async getMe(): Promise<User> {
    const response = await apiClient.get<ApiResponse<User>>('/auth/me');

    if (!response.data.success || !response.data.data) {
      throw new Error(response.data.message || 'Failed to retrieve user profile');
    }

    return response.data.data;
  },

  /**
   * Fetch profile directly using a specific access token (used during initial session restoration).
   */
  async getMeWithToken(accessToken: string): Promise<User> {
    const response = await apiClient.get<ApiResponse<User>>('/auth/me', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.data.success || !response.data.data) {
      throw new Error(response.data.message || 'Failed to retrieve user profile');
    }

    return response.data.data;
  },
};

