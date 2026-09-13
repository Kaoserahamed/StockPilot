'use client';
import { createContext, useCallback, useContext, useState } from 'react';

type ToastTone = 'success' | 'error' | 'info' | 'warning';
type Toast = { id: number; message: string; tone: ToastTone };

type ToastCtx = {
  notify: (message: string, tone?: ToastTone) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
};

const Ctx = createContext<ToastCtx>({} as any);
let _id = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const notify = useCallback((message: string, tone: ToastTone = 'info') => {
    const id = ++_id;
    setToasts((prev) => [...prev, { id, message, tone }]);
    // Auto-dismiss after 4 seconds
    setTimeout(() => dismiss(id), 4000);
  }, [dismiss]);

  const ctx: ToastCtx = {
    notify,
    success: (m) => notify(m, 'success'),
    error: (m) => notify(m, 'error'),
    info: (m) => notify(m, 'info'),
    warning: (m) => notify(m, 'warning'),
  };

  return (
    <Ctx.Provider value={ctx}>
      {children}
      {/* Toast container — fixed bottom-right */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((t) => {
          const colors: Record<ToastTone, string> = {
            success: 'bg-emerald-600 text-white',
            error: 'bg-rose-600 text-white',
            info: 'bg-slate-800 text-white',
            warning: 'bg-amber-500 text-white',
          };
          const icons: Record<ToastTone, string> = {
            success: '✓', error: '✕', info: 'ℹ', warning: '⚠',
          };
          return (
            <div key={t.id} className={`flex items-center gap-2.5 rounded-xl px-4 py-3 text-sm font-medium shadow-lg ${colors[t.tone]}`}>
              <span className="text-base">{icons[t.tone]}</span>
              <span className="max-w-xs">{t.message}</span>
              <button onClick={() => dismiss(t.id)} className="ml-2 opacity-70 hover:opacity-100">✕</button>
            </div>
          );
        })}
      </div>
    </Ctx.Provider>
  );
}

export const useToast = () => useContext(Ctx);
