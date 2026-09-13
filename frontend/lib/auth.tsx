'use client';
import { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from './api';

type User = { id: number; name: string; email?: string | null; phone?: string | null; is_active: boolean };
type Ctx = {
  user: User | null; loading: boolean;
  login(u: string, p: string): Promise<void>;
  register(payload: any): Promise<void>;
  logout(): void;
  refresh(): Promise<void>;
};

const AuthCtx = createContext<Ctx>({} as any);
export const useAuth = () => useContext(AuthCtx);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refresh = async () => {
    const t = typeof window !== 'undefined' ? localStorage.getItem('pos_token') : null;
    if (!t) { setUser(null); setLoading(false); return; }
    try {
      const r = await api.get('/auth/me');
      setUser(r.data);
    } catch { setUser(null); localStorage.removeItem('pos_token'); }
    setLoading(false);
  };

  useEffect(() => { refresh(); }, []);

  const login = async (username: string, password: string) => {
    const r = await api.post('/auth/login', { username, password });
    localStorage.setItem('pos_token', r.data.access_token);
    await refresh();
    router.push('/dashboard');
  };

  const register = async (payload: any) => {
    await api.post('/auth/register', payload);
    await login(payload.email || payload.phone, payload.password);
  };

  const logout = async () => {
    try { await api.post('/auth/logout'); } catch {}
    localStorage.removeItem('pos_token');
    setUser(null);
    router.push('/login');
  };

  return <AuthCtx.Provider value={{ user, loading, login, register, logout, refresh }}>{children}</AuthCtx.Provider>;
}
