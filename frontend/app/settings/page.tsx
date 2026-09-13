'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Btn, Card, Field, Input, PageTitle } from '@/components/ui';

export default function SettingsPage() {
  const [msg, setMsg] = useState('');
  const q = useQuery({ queryKey: ['settings'], queryFn: async () => (await api.get('/settings')).data });
  const biz = useQuery({ queryKey: ['biz2'], queryFn: async () => (await api.get('/businesses/me')).data });
  const [f, setF] = useState<any>(null);
  const cur = f || q.data || {};

  const save = async () => {
    setMsg('');
    try {
      await api.patch('/settings', { currency: cur.currency, tax_rate: Number(cur.tax_rate || 0), invoice_format: cur.invoice_format, min_stock_default: Number(cur.min_stock_default || 0), business_name: cur.business_name, address: cur.address, phone: cur.phone, email: cur.email });
      q.refetch(); setF(null); setMsg('Settings saved.');
    } catch (e) { setMsg(errMsg(e)); }
  };
  const set = (k: string, v: string) => setF((s: any) => ({ ...(s || q.data || {}), [k]: v }));

  return (
    <Shell>
      <PageTitle title="Settings" sub="Business profile, currency, tax and defaults." />
      {msg && <div className="mb-3 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h3 className="font-bold">Business profile</h3>
          <div className="mt-3 space-y-2.5">
            <Field label="Shop name"><Input value={cur.business_name ?? biz.data?.name ?? ''} onChange={(e) => set('business_name', e.target.value)} /></Field>
            <Field label="Address"><Input value={cur.address ?? ''} onChange={(e) => set('address', e.target.value)} /></Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Phone"><Input value={cur.phone ?? ''} onChange={(e) => set('phone', e.target.value)} /></Field>
              <Field label="Email"><Input value={cur.email ?? ''} onChange={(e) => set('email', e.target.value)} /></Field>
            </div>
          </div>
        </Card>
        <Card>
          <h3 className="font-bold">Preferences</h3>
          <div className="mt-3 space-y-2.5">
            <div className="grid grid-cols-2 gap-2">
              <Field label="Currency"><Input value={cur.currency ?? ''} onChange={(e) => set('currency', e.target.value)} /></Field>
              <Field label="Tax rate"><Input value={String(cur.tax_rate ?? '')} onChange={(e) => set('tax_rate', e.target.value)} /></Field>
            </div>
            <Field label="Invoice format"><Input value={cur.invoice_format ?? ''} onChange={(e) => set('invoice_format', e.target.value)} /></Field>
            <Field label="Default min stock"><Input value={String(cur.min_stock_default ?? '')} onChange={(e) => set('min_stock_default', e.target.value)} /></Field>
            <Btn onClick={save} className="w-full">Save settings</Btn>
          </div>
        </Card>
      </div>
    </Shell>
  );
}
