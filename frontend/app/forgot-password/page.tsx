'use client';
import { useState } from 'react';
import Link from 'next/link';
import { api, errMsg } from '@/lib/api';
import { Btn, Card, Field, Input } from '@/components/ui';

export default function Forgot() {
  const [u, setU] = useState('');
  const [token, setToken] = useState('');
  const [np, setNp] = useState('');
  const [msg, setMsg] = useState('');

  return (
    <main className="mx-auto max-w-md space-y-4 p-6">
      <Card className="!p-6">
        <h1 className="text-xl font-extrabold tracking-tight">Reset your password</h1>
        <p className="mt-1 text-sm text-slate-500">We&apos;ll help you get back into your workspace.</p>
        <div className="mt-4 space-y-3">
          <Field label="Account email or phone"><Input value={u} onChange={(e) => setU(e.target.value)} placeholder="you@shop.com" /></Field>
          <Btn variant="secondary" onClick={async () => {
            try { const r = await api.post('/auth/forgot-password', { username: u }); setToken(r.data?.dev_token || ''); setMsg('If the account exists, reset instructions have been sent.'); }
            catch (e) { setMsg(errMsg(e)); }
          }}>Send reset link</Btn>
        </div>
      </Card>
      <Card className="!p-6">
        <h2 className="font-bold">Have a reset code?</h2>
        <div className="mt-3 space-y-3">
          <Field label="Reset code"><Input value={token} onChange={(e) => setToken(e.target.value)} placeholder="Paste the code here" /></Field>
          <Field label="New password"><Input type="password" value={np} onChange={(e) => setNp(e.target.value)} placeholder="Choose a strong password" /></Field>
          <Btn className="w-full" onClick={async () => {
            try { await api.post('/auth/reset-password', { token, new_password: np }); setMsg('Password updated. You can now sign in.'); }
            catch (e) { setMsg(errMsg(e)); }
          }}>Update password</Btn>
        </div>
      </Card>
      {msg && <div className="rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      <div className="text-center text-sm"><Link href="/login" className="font-semibold text-emerald-700 hover:underline">Back to sign in</Link></div>
    </main>
  );
}
