import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  ReactNode,
} from "react";
import { api } from "../api/client";

export interface Account {
  id: string;
  email: string;
  display_name: string | null;
  role: "customer" | "admin" | "superadmin";
  status: "active" | "suspended" | "cancelled" | "pending";
  plan: "starter" | "pro" | "enterprise";
  totp_enabled: boolean;
  created_at: string;
  updated_at: string;
}

interface AuthContextValue {
  account: Account | null;
  token: string | null;
  isLoading: boolean;
  isAdmin: boolean;
  isSuperadmin: boolean;
  login: (email: string, password: string) => Promise<{ totp_required?: boolean; temp_token?: string }>;
  loginTotp: (tempToken: string, code: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  impersonate: (token: string) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [account, setAccount] = useState<Account | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem("access_token"));
  const [isLoading, setIsLoading] = useState(true);

  const isAdmin = account?.role === "admin" || account?.role === "superadmin";
  const isSuperadmin = account?.role === "superadmin";

  const refresh = useCallback(async () => {
    const t = localStorage.getItem("access_token");
    if (!t) {
      // Check for impersonation token in URL
      const params = new URLSearchParams(window.location.search);
      const impToken = params.get("impersonate_token");
      if (impToken) {
        localStorage.setItem("access_token", impToken);
        window.history.replaceState({}, document.title, window.location.pathname);
      } else {
        setIsLoading(false);
        return;
      }
    }
    const token = localStorage.getItem("access_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const res = await api.get<{ id: string; email: string; display_name: string | null; role: string; status: string; plan: string; totp_enabled: boolean; created_at: string; updated_at: string }>("/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const acc = res.data as Account;
      setAccount(acc);
      setToken(token);
    } catch {
      localStorage.removeItem("access_token");
      setAccount(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = async (email: string, password: string) => {
    const res = await api.post<{
      access_token?: string;
      token_type?: string;
      account?: Account;
      totp_required?: boolean;
      temp_token?: string;
    }>("/auth/login", { email, password });
    if (res.data.totp_required && res.data.temp_token) {
      return { totp_required: true, temp_token: res.data.temp_token };
    }
    if (res.data.access_token) {
      localStorage.setItem("access_token", res.data.access_token);
      setToken(res.data.access_token);
      setAccount(res.data.account ?? null);
    }
    return {};
  };

  const loginTotp = async (tempToken: string, code: string) => {
    const res = await api.post<{
      access_token: string;
      token_type: string;
      account: Account;
    }>("/auth/login/totp", { temp_token: tempToken, code });
    localStorage.setItem("access_token", res.data.access_token);
    setToken(res.data.access_token);
    setAccount(res.data.account);
  };

  const register = async (email: string, password: string, displayName?: string) => {
    const res = await api.post<Account>("/auth/register", {
      email,
      password,
      display_name: displayName || null,
    });
    setAccount(res.data);
    // Auto-login after register
    const loginRes = await api.post<{ access_token: string; account: Account }>("/auth/login", { email, password });
    localStorage.setItem("access_token", loginRes.data.access_token);
    setToken(loginRes.data.access_token);
    setAccount(loginRes.data.account);
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // ignore
    }
    localStorage.removeItem("access_token");
    setToken(null);
    setAccount(null);
  };

  const impersonate = (impersonateToken: string) => {
    localStorage.setItem("access_token", impersonateToken);
    setToken(impersonateToken);
    refresh();
  };

  return (
    <AuthContext.Provider
      value={{
        account,
        token,
        isLoading,
        isAdmin,
        isSuperadmin,
        login,
        loginTotp,
        register,
        logout,
        refresh,
        impersonate,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
