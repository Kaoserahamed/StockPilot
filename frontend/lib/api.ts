import axios from 'axios';

const base = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export const api = axios.create({ baseURL: `${base}/api/v1` });

if (typeof window !== 'undefined') {
  api.interceptors.request.use((cfg) => {
    const t = localStorage.getItem('pos_token');
    const b = localStorage.getItem('pos_business_id');
    if (t) cfg.headers.Authorization = `Bearer ${t}`;
    if (b) (cfg.headers as any)['X-Business-Id'] = b;
    return cfg;
  });
  api.interceptors.response.use(
    (r) => r,
    (e) => {
      if (e?.response?.status === 401 && window.location.pathname !== '/login') {
        localStorage.removeItem('pos_token');
        window.location.href = '/login';
      }
      return Promise.reject(e);
    }
  );
}

export function errMsg(e: any, fallback = 'Request failed'): string {
  const d = e?.response?.data;
  if (!d) return e?.message || fallback;
  if (typeof d === 'string') return d;
  if (typeof d?.detail === 'string') return d.detail;
  if (Array.isArray(d?.detail)) return d.detail.map((x: any) => x?.msg || JSON.stringify(x)).join('; ');
  return JSON.stringify(d);
}

export async function downloadBlob(path: string, filename: string) {
  const res = await api.get(path, { responseType: 'blob' });
  const url = URL.createObjectURL(new Blob([res.data]));
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}
