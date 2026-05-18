import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { isUnauthenticatedError, isApiHttpError, ApiHttpError } from "../../shared/api/errors";
import type { AuthError, User } from "../../entities/user/model/types";
import { fetchCurrentUser } from "../../entities/user/api/userApi";
import { login as loginApi } from "../../features/auth-login/api";
import { logout as logoutApi } from "../../features/auth-logout/api";

type AuthState = {
  currentUser: User | null;
  loading: boolean;
  error: AuthError | null;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshCurrentUser: () => Promise<void>;
  clearAuthError: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

function normalizeAuthError(error: unknown): AuthError {
  if (isApiHttpError(error)) {
    return { code: error.code, message: error.safeMessage };
  }
  if (error instanceof Error) {
    return { code: "client_error", message: error.message };
  }
  return { code: "unknown", message: "请求失败，请稍后再试" };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<AuthError | null>(null);

  const refreshCurrentUser = useCallback(async () => {
    setLoading(true);
    try {
      const user = await fetchCurrentUser();
      setCurrentUser(user);
      setError(null);
    } catch (err) {
      if (isUnauthenticatedError(err)) {
        setCurrentUser(null);
        setError(null);
      } else if (isApiHttpError(err)) {
        const httpError = err as ApiHttpError;
        setError({ code: httpError.code, message: httpError.safeMessage });
        setCurrentUser(null);
      } else {
        setError(normalizeAuthError(err));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshCurrentUser();
  }, [refreshCurrentUser]);

  const login = useCallback(
    async (identifier: string, password: string) => {
      setLoading(true);
      try {
        const user = await loginApi({ identifier, password });
        setCurrentUser(user);
        setError(null);
      } catch (err) {
        const normalized = normalizeAuthError(err);
        setError(normalized);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [setCurrentUser],
  );

  const logout = useCallback(async () => {
    setLoading(true);
    try {
      await logoutApi();
    } catch (err) {
      setError(normalizeAuthError(err));
    } finally {
      setCurrentUser(null);
      setLoading(false);
    }
  }, []);

  const clearAuthError = useCallback(() => setError(null), []);

  const value = useMemo(
    () => ({
      currentUser,
      loading,
      error,
      login,
      logout,
      refreshCurrentUser,
      clearAuthError,
    }),
    [currentUser, loading, error, login, logout, refreshCurrentUser, clearAuthError],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (ctx === null) {
    throw new Error("useAuth 必须在 AuthProvider 内部使用");
  }
  return ctx;
}
