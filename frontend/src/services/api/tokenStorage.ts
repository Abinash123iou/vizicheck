/**
 * Session storage manager for refresh tokens.
 *
 * Rules:
 * - Refresh tokens are stored ONLY in sessionStorage (tab-scoped).
 * - Access tokens are NEVER stored in sessionStorage or localStorage (kept in Zustand memory).
 * - Passwords are NEVER persisted anywhere.
 */

const REFRESH_TOKEN_KEY = 'vizicheck_refresh_token';

export const tokenStorage = {
  getRefreshToken(): string | null {
    if (typeof window === 'undefined' || !window.sessionStorage) {
      return null;
    }
    try {
      return window.sessionStorage.getItem(REFRESH_TOKEN_KEY);
    } catch {
      return null;
    }
  },

  setRefreshToken(token: string): void {
    if (typeof window === 'undefined' || !window.sessionStorage) {
      return;
    }
    try {
      window.sessionStorage.setItem(REFRESH_TOKEN_KEY, token);
    } catch {
      // Storage quota or security error
    }
  },

  clearRefreshToken(): void {
    if (typeof window === 'undefined' || !window.sessionStorage) {
      return;
    }
    try {
      window.sessionStorage.removeItem(REFRESH_TOKEN_KEY);
    } catch {
      // Ignore
    }
  },
};

