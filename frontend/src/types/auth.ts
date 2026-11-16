export type RoleName = 
  | 'SUPER_ADMIN' 
  | 'TENANT_ADMIN' 
  | 'HOST_USER' 
  | 'SECURITY_OFFICER' 
  | 'RECEPTIONIST';

export interface Role {
  id: number;
  name: RoleName;
  description?: string;
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string | null;
  role_id: number;
  role_name: RoleName;
  role?: Role;
  tenant_id: number | null;
  tenant_name?: string | null;
  permissions?: string[];
  is_active: boolean;
  last_login?: string | null;
  created_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponseData {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface TokenResponseData {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in?: number;
}

// Backward-compatible alias for existing imports
export type RefreshTokenResponseData = TokenResponseData;
