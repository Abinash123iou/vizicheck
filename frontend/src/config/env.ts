export const ENV = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  PROJECT_NAME: 'ViziCheck',
  STORAGE_KEYS: {
    ACCESS_TOKEN: 'vizicheck_access_token',
    REFRESH_TOKEN: 'vizicheck_refresh_token',
    USER: 'vizicheck_user',
  },
} as const;

