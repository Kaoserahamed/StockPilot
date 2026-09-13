import React from 'react';

export function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.05),0_12px_32px_-16px_rgba(15,23,42,0.18)] ${className}`}>
      {children}
    </div>
  );
}

export function SectionTitle({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="mb-3">
      <h3 className="text-base font-bold tracking-tight text-slate-900">{title}</h3>
      {sub && <p className="mt-0.5 text-sm text-slate-500">{sub}</p>}
    </div>
  );
}

export function Stat({ label, value, sub, accent = 'emerald' }: { label: string; value: any; sub?: string; accent?: 'emerald' | 'teal' | 'amber' | 'rose' | 'indigo' }) {
  const bar: Record<string, string> = {
    emerald: 'from-emerald-500 to-teal-500',
    teal: 'from-teal-500 to-cyan-500',
    amber: 'from-amber-500 to-orange-500',
    rose: 'from-rose-500 to-pink-500',
    indigo: 'from-indigo-500 to-violet-500',
  };
  return (
    <Card className="relative overflow-hidden !p-0">
      <div className={`h-1 w-full bg-gradient-to-r ${bar[accent]}`} />
      <div className="p-4">
        <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">{label}</div>
        <div className="mt-1 text-[26px] font-extrabold tabular-nums text-slate-900">{value}</div>
        {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
      </div>
    </Card>
  );
}

type BtnVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export function Btn(props: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: BtnVariant }) {
  const { variant = 'primary', className = '', ...rest } = props;
  const cls =
    variant === 'primary'
      ? 'bg-emerald-600 text-white shadow-[0_8px_20px_-8px_rgba(5,150,105,0.7)] hover:bg-emerald-700'
      : variant === 'secondary'
        ? 'border border-slate-200 bg-white text-slate-800 hover:border-emerald-300 hover:bg-emerald-50'
        : variant === 'danger'
          ? 'bg-rose-600 text-white hover:bg-rose-700'
          : 'bg-slate-900/[0.04] text-slate-800 hover:bg-slate-900/[0.08]';
  return <button {...rest} className={`inline-flex items-center justify-center rounded-xl px-3.5 py-2.5 text-sm font-semibold transition disabled:opacity-50 ${cls} ${className}`} />;
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/15 ${props.className || ''}`} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={`w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-emerald-500 ${props.className || ''}`} />;
}

export function PageTitle({ title, sub, right }: { title: string; sub?: string; right?: React.ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-[26px] font-extrabold tracking-tight text-slate-900">{title}</h1>
        {sub && <p className="mt-1 max-w-2xl text-sm text-slate-500">{sub}</p>}
      </div>
      <div className="flex flex-wrap items-center gap-2">{right}</div>
    </div>
  );
}

export function Badge({ children, tone = 'slate' }: { children: React.ReactNode; tone?: 'slate' | 'green' | 'red' | 'amber' | 'blue' }) {
  const map: any = {
    slate: 'bg-slate-100 text-slate-700', green: 'bg-emerald-100 text-emerald-800',
    red: 'bg-rose-100 text-rose-800', amber: 'bg-amber-100 text-amber-800', blue: 'bg-cyan-100 text-cyan-900',
  };
  return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${map[tone]}`}>{children}</span>;
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-semibold text-slate-600">{label}</span>
      {children}
    </label>
  );
}

export function Empty({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center">
      <div className="text-sm font-semibold text-slate-700">{title}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}

export function TableWrap({ children }: { children: React.ReactNode }) {
  return <div className="overflow-hidden rounded-xl border border-slate-200">{children}</div>;
}

// ---------- Form validation components ----------
export function FormError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="mt-1 text-xs font-medium text-rose-600">{message}</p>;
}

export function ValidatedInput(props: React.InputHTMLAttributes<HTMLInputElement> & { error?: string }) {
  const { error, className = '', ...rest } = props;
  return (
    <div>
      <input
        {...rest}
        className={`w-full rounded-xl border px-3.5 py-2.5 text-sm outline-none transition ${
          error
            ? 'border-rose-300 focus:border-rose-500 focus:ring-4 focus:ring-rose-500/15'
            : 'border-slate-200 focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/15'
        } ${className}`}
      />
      <FormError message={error} />
    </div>
  );
}
