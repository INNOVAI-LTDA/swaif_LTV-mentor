import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { clearAccessToken, getAccessToken } from "../lib/authStorage.js";
import { onUnauthorized } from "../lib/httpEvents.js";
import { getMe, login as loginService } from "../services/authService.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [accessToken, setAccessTokenState] = useState(getAccessToken());
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  const refreshMe = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      return null;
    }

    setLoading(true);
    try {
      const me = await getMe();
      setUser(me);
      return me;
    } catch {
      clearAccessToken();
      setAccessTokenState(null);
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (email, password) => {
    const credentials =
      typeof email === "object" && email !== null
        ? email
        : { email, password };

    const payload = await loginService(credentials);
    setAccessTokenState(payload?.access_token || null);
    await refreshMe();
    return payload;
  }, [refreshMe]);

  const logout = useCallback(() => {
    clearAccessToken();
    setAccessTokenState(null);
    setUser(null);
  }, []);

  useEffect(() => {
    const unsubscribe = onUnauthorized(() => {
      clearAccessToken();
      setAccessTokenState(null);
      setUser(null);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  useEffect(() => {
    if (accessToken) {
      refreshMe();
    }
  }, [accessToken, refreshMe]);

  const value = useMemo(
    () => ({
      accessToken,
      user,
      loading,
      isAuthenticated: Boolean(accessToken),
      login,
      logout,
      refreshMe,
    }),
    [accessToken, user, loading, login, logout, refreshMe]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context) return context;

  // Fallback for screens rendered without provider.
  return {
    accessToken: getAccessToken(),
    user: null,
    loading: false,
    isAuthenticated: Boolean(getAccessToken()),
    login: async () => null,
    logout: () => clearAccessToken(),
    refreshMe: async () => null,
  };
}
