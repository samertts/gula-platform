export interface ApiResponse<T = unknown> {
  data?: T;
  message?: string;
  message_ar?: string;
  error?: string;
  detail?: string | { message: string; message_ar: string };
  request_id?: string;
}

export interface PaginatedResponse<T> {
  total: number;
  skip: number;
  limit: number;
  items?: T[];
  results?: T[];
  data?: T[];
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  access_token?: string;
  refresh_token: string;
  token_type: string;
  user: UserInfo;
}

export interface UserInfo {
  id: number;
  name: string;
  email: string;
  role: string;
  lab_id: number | null;
  lab_name: string | null;
}

export interface JwtPayload {
  user_id: number;
  lab_id: number | null;
  role: string;
  perm_ver: number;
  type: string;
  jti: string;
  exp: number;
}
