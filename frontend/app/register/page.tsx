'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { errMsg } from '@/lib/api';
import { Btn, Card, Field, Input } from '@/components/ui';

export default function Register() {
  const { register } = useAuth();
  const [f, setF] = useState({ owner_name: '', email: '', password: '', business_name: '', business_address: '' });
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (k: string, v: string) => setF((s) => ({ ...s, [k]: v }));

  return (
    <main className="mx-auto max-w-xl p-6">
      <Card className="!p-7">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-600 text-xl font-black text-white">S</div>
        <h1 className="mt-4 text-2xl font-extrabold tracking-tight">Create your workspace</h1>
        <p className="mt-1 text-sm text-slate-500">Set up your account and shop profile in under two minutes.</p>
        <div className="mt-5 grid gap-3.5 sm:grid-cols-2">
          <Field label="Your name"><Input value={f.owner_name} onChange={(e) => set('owner_name', e.target.value)} placeholder="Ayesha Rahman" /></Field>
          <Field label="Email"><Input value={f.email} onChange={(e) => set('email', e.target.value)} placeholder="you@shop.com" /></Field>
          <Field label="Password"><Input type="password" value={f.password} onChange={(e) => set('password', e.target.value)} placeholder="Min 8 chars, upper + lower + digit + symbol" /></Field>
          <Field label="Shop name"><Input value={f.business_name} onChange={(e) => set('business_name', e.target.value)} placeholder="Rahman Store" /></Field>
          <div className="sm:col-span-2"><Field label="Shop address"><Input value={f.business_address} onChange={(e) => set('business_address', e.target.value)} placeholder="Street, area, city" /></Field></div>
        </div>
        {err && <div className="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{err}</div>}
        <Btn className="mt-5 w-full !py-3" disabled={busy} onClick={async () => { setBusy(true); setErr(''); try { await register(f); } catch (e) { setErr(errMsg(e)); } setBusy(false); }}>
          {busy ? 'Creating…' : 'Create account & continue'}
        </Btn>
        <div className="mt-3 text-center text-sm"><Link href="/login" className="font-semibold text-emerald-700 hover:underline">Already have an account? Sign in</Link></div>
      </Card>
    </main>
  );
}
