'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Btn, Card, Empty, PageTitle } from '@/components/ui';

export default function SubscriptionPage() {
  const [msg, setMsg] = useState('');
  const q = useQuery({ queryKey: ['sub'], queryFn: async () => (await api.get('/subscription')).data });

  const change = async (plan: string) => {
    setMsg('');
    try { await api.patch('/subscription', { plan }); q.refetch(); setMsg(`Plan changed to ${plan}.`); }
    catch (e) { setMsg(errMsg(e)); }
  };

  const d = q.data;
  return (
    <Shell>
      <PageTitle title="Billing" sub="Plan, usage and limits." />
      {msg && <div className="mb-3 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <div className="text-xs font-bold uppercase text-slate-500">Current plan</div>
          <div className="mt-1 text-3xl font-extrabold capitalize">{d?.plan || '—'}</div>
          <div className="mt-1 text-sm text-slate-500">Status: {d?.status || '—'}</div>
          {d?.message && <div className="mt-2 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800">{d.message}</div>}
          <div className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between"><span>Products</span><span className="font-bold">{d?.product_count ?? '—'} / {d?.product_limit ?? '—'} ({d?.product_usage_pct ?? 0}%)</span></div>
            <div className="flex justify-between"><span>Team</span><span className="font-bold">{d?.employee_count ?? '—'} / {d?.employee_limit ?? '—'} ({d?.employee_usage_pct ?? 0}%)</span></div>
          </div>
        </Card>
        {['free', 'basic', 'pro'].map((p) => (
          <Card key={p}>
            <div className="text-lg font-extrabold capitalize">{p}</div>
            <div className="mt-1 text-sm text-slate-500">{p === 'free' ? '100 products · 5 team' : p === 'basic' ? '1,000 products · 25 team' : '100k products · 1k team'}</div>
            <Btn variant={d?.plan === p ? 'ghost' : 'primary'} disabled={d?.plan === p} onClick={() => change(p)} className="mt-3 w-full">{d?.plan === p ? 'Current plan' : `Switch to ${p}`}</Btn>
          </Card>
        ))}
      </div>
      {!d && <div className="mt-3"><Empty title="Loading plan…" /></div>}
    </Shell>
  );
}
