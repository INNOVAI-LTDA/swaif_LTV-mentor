import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { getMe, login as loginService, logout as logoutService } from "../../domain/services/authService";
import type { AuthSession } from "../../domain/models";
import { toUserErrorMessage } from "../../shared/api/types";
import { onUnauthorized } from "../../shared/auth/authEvents";
import { clearAccessToken, getAccessToken } from "../../shared/auth/tokenStorage";

type PreviewRole = "admin" | "mentor" | "aluno";

type PreviewSession = {
  email: string;
  role: PreviewRole;
  token: string;
};

type AuthContextValue = {
  accessToken: string | null;
  user: AuthSession["user"];
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  isPreviewSession: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  loginPreview: (email: string, role: PreviewRole) => void;
  logout: () => void;
  refreshMe: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const PREVIEW_SESSION_KEY = "swaif_mvp_preview_session";

function hasLocalStorage(): boolean {
  return typeof localStorage !== "undefined";
}

function getPreviewSession(): PreviewSession | null {
  if (!hasLocalStorage()) {
    return null;
  }

  const raw = localStorage.getItem(PREVIEW_SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as PreviewSession;
  } catch {
    localStorage.removeItem(PREVIEW_SESSION_KEY);
    return null;
  }
}

function setPreviewSession(session: PreviewSession): void {
  if (!hasLocalStorage()) {
    return;
  }

  localStorage.setItem(PREVIEW_SESSION_KEY, JSON.stringify(session));
}

function clearPreviewSession(): void {
  if (!hasLocalStorage()) {
    return;
  }

  localStorage.removeItem(PREVIEW_SESSION_KEY);
}

function toPreviewUser(session: PreviewSession): NonNullable<AuthSession["user"]> {
  return {
    id: `preview-${session.role}`,
    email: session.email,
    role: session.role
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const initialPreviewSession = getPreviewSession();
  const [accessToken, setAccessToken] = useState<string | null>(initialPreviewSession?.token ?? getAccessToken());
  const [user, setUser] = useState<AuthSession["user"]>(initialPreviewSession ? toPreviewUser(initialPreviewSession) : null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshMe = useCallback(async () => {
    const previewSession = getPreviewSession();
    if (previewSession) {
      setAccessToken(previewSession.token);
      setUser(toPreviewUser(previewSession));
      setError(null);
      return;
    }

    if (!getAccessToken()) {
      setAccessToken(null);
      setUser(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const me = await getMe();
      setAccessToken(getAccessToken());
      setUser(me);
    } catch (err) {
      setAccessToken(null);
      setUser(null);
      setError(toUserErrorMessage(err, "Falha ao validar sessao."));
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    clearPreviewSession();
    setLoading(true);
    setError(null);

    try {
      const session = await loginService({ email, password });
      setAccessToken(session.accessToken);
      setUser(session.user);
      return true;
    } catch (err) {
      setAccessToken(null);
      setUser(null);
      setError(toUserErrorMessage(err, "Falha ao autenticar."));
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const loginPreview = useCallback((email: string, role: PreviewRole) => {
    const previewSession: PreviewSession = {
      email,
      role,
      token: `preview-${role}-token`
    };

    setPreviewSession(previewSession);
    setAccessToken(previewSession.token);
    setUser(toPreviewUser(previewSession));
    setError(null);
  }, []);

  const logout = useCallback(() => {
    logoutService();
    clearPreviewSession();
    clearAccessToken();
    setAccessToken(null);
    setUser(null);
    setError(null);
  }, []);

  useEffect(() => {
    const unsubscribe = onUnauthorized(() => {
      clearPreviewSession();
      clearAccessToken();
      setAccessToken(null);
      setUser(null);
    });

    return unsubscribe;
  }, []);

  useEffect(() => {
    if (accessToken && !getPreviewSession()) {
      void refreshMe();
    }
  }, [accessToken, refreshMe]);

  const value = useMemo<AuthContextValue>(
    () => ({
      accessToken,
      user,
      loading,
      error,
      isAuthenticated: Boolean(accessToken),
      isPreviewSession: Boolean(getPreviewSession()),
      login,
      loginPreview,
      logout,
      refreshMe
    }),
    [accessToken, user, loading, error, login, loginPreview, logout, refreshMe]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth precisa de AuthProvider no topo da aplicacao.");
  }
  return context;
}
