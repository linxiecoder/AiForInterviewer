export interface User {
  user_id: string;
  owner_id: string;
  email: string;
  username: string;
  display_name: string;
  roles: string[];
  session_expires_at?: string | null;
}

export interface AuthError {
  code: string;
  message: string;
}
