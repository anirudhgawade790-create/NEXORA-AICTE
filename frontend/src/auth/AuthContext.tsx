import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { apiGet, apiPost } from '../api/client';

export type AppUser = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  region: string | null;
  institution_id: number | null;
  is_active: boolean;
};

type AuthContextValue = {
  user: AppUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; full_name: string; institution_id: number }) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(() => {
    const cached = localStorage.getItem('nexora_user');
    return cached ? JSON.parse(cached) as AppUser : null;
  });
  const [loading, setLoading] = useState(Boolean(localStorage.getItem('nexora_token')));

  useEffect(() => {
    if (!localStorage.getItem('nexora_token')) {
      setLoading(false);
      return;
    }
    apiGet<AppUser>('/auth/me')
      .then((current) => {
        setUser(current);
        localStorage.setItem('nexora_user', JSON.stringify(current));
      })
      .catch(() => {
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const result = await apiPost<{ access_token: string; user: AppUser }>('/auth/login', { email, password });
    localStorage.setItem('nexora_token', result.access_token);
    localStorage.setItem('nexora_user', JSON.stringify(result.user));
    setUser(result.user);
  };
  const register = async (data: { email: string; password: string; full_name: string; institution_id: number }) => {
    await apiPost('/auth/register', data);
  };
  const logout = () => {
      localStorage.removeItem('nexora_token');
      localStorage.removeItem('nexora_user');
      setUser(null);
      window.location.assign('/login');
  };
  const value = useMemo<AuthContextValue>(() => ({
    user, loading, login, register, logout,
  }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
