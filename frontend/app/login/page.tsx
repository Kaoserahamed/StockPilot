'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { errMsg } from '@/lib/api';
import { Btn, Card, Field, Input } from '@/components/ui';

export default function Login() {
  const { login } = useAuth();
  const [u, setU] = useState('');
  const [p, setP] = useState('');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl items-center justify-center p-6">
      <div className="grid w-full overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_24px_60px_-24px_rgba(15,23,42,0.25)] md:grid-cols-2">
        <div className="hidden bg-slate-950 p-8 text-white md:block">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-600 text-xl font-black">S</div>
          <h2 className="mt-6 text-3xl font-extrabold leading-tight">Welcome back to your counter.</h2>
          <p className="mt-3 text-sm leading-relaxed text-slate-300">Check today&apos;s sales, finish pending invoices and keep stock accurate — all from one calm dashboard.</p>
          <div className="mt-6 space-y-2 text-sm">
            {['Live sales & profit overview', 'Low-stock and dues reminders', 'One-click invoice PDF downloads'].map((t) => (
              <div key={t} className="flex items-center gap-2"><span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-xs">✓</span>{t}</div>
            ))}
          </div>
        </div>
        <div className="p-7">
          <h1 className="text-2xl font-extrabold tracking-tight">Sign in</h1>
          <p className="mt-1 text-sm text-slate-500">Use your account email or phone number.</p>
          <div className="mt-5 space-y-3.5">
            <Field label="Email or phone"><Input value={u} onChange={(e) => setU(e.target.value)} placeholder="you@shop.com" /></Field>
            <Field label="Password"><Input type="password" value={p} onChange={(e) => setP(e.target.value)} placeholder="••••••••" /></Field>
            {err && <div className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{err}</div>}
            <Btn className="w-full !py-3" disabled={busy || !u || !p} onClick={async () => { setBusy(true); setErr(''); try { await login(u, p); } catch (e) { setErr(errMsg(e)); } setBusy(false); }}>
              {busy ? 'Signing in…' : 'Sign in'}
            </Btn>
            <div className="flex justify-between text-sm">
              <Link href="/register" className="font-semibold text-emerald-700 hover:underline">Create account</Link>
              <Link href="/forgot-password" className="font-semibold text-emerald-700 hover:underline">Forgot password?</Link>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
