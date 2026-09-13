'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Badge, Btn, Card, Empty, Field, Input, PageTitle, TableWrap } from '@/components/ui';

export default function PurchasesPage() {
  const [form, setForm] = useState({ supplier_id: '', product_id: '', qty: '1', cost: '' });
  const [msg, setMsg] = useState('');
  const sups = useQuery({ queryKey: ['sups'], queryFn: async () => (await api.get('/suppliers')).data });
  const prods = useQuery({ queryKey: ['prods'], queryFn: async () => (await api.get('/products')).data });
  const list = useQuery({ queryKey: ['purchases'], queryFn: async () => (await api.get('/purchases')).data });
  const set = (k: string, v: string) => setForm((s) => ({ ...s, [k]: v }));

  const create = async () => {
    setMsg('');
    try {
      await api.post('/purchases', { supplier_id: Number(form.supplier_id), items: [{ product_id: Number(form.product_id), quantity: Number(form.qty), unit_cost: Number(form.cost) }] });
      list.refetch(); setMsg('Purchase recorded and stock updated.');
    } catch (e) { setMsg(errMsg(e)); }
  };

  return (
    <Shell>
      <PageTitle title="Purchases" sub="Supplier orders and stock intake." />
      {msg && <div className="mb-3 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h3 className="font-bold">New purchase</h3>
          <div className="mt-3 space-y-2.5">
            <Field label="Supplier"><select value={form.supplier_id} onChange={(e) => set('supplier_id', e.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"><option value="">Select…</option>{(sups.data || []).map((s: any) => <option key={s.id} value={s.id}>{s.company_name}</option>)}</select></Field>
            <Field label="Product"><select value={form.product_id} onChange={(e) => set('product_id', e.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"><option value="">Select…</option>{(prods.data || []).map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Qty"><Input value={form.qty} onChange={(e) => set('qty', e.target.value)} /></Field>
              <Field label="Unit cost"><Input value={form.cost} onChange={(e) => set('cost', e.target.value)} /></Field>
            </div>
            <Btn onClick={create} disabled={!form.supplier_id || !form.product_id || !form.cost} className="w-full">Save purchase</Btn>
          </div>
        </Card>
        <Card className="lg:col-span-2">
          {list.isLoading ? <div className="h-24 animate-pulse rounded-xl bg-slate-100" /> : !(list.data || []).length ? <Empty title="No purchases yet" /> : (
            <TableWrap><table className="w-full text-sm"><thead><tr className="bg-slate-50 text-left text-xs text-slate-500"><th className="px-3 py-2">ID</th><th className="px-3 py-2">Supplier</th><th className="px-3 py-2">Total</th><th className="px-3 py-2">Status</th></tr></thead>
              <tbody>{(list.data || []).map((p: any) => (
                <tr key={p.id} className="border-t border-slate-100"><td className="px-3 py-2">#{p.id}</td><td className="px-3 py-2">{p.supplier_name}</td><td className="px-3 py-2">{p.total_amount}</td><td className="px-3 py-2"><Badge tone={p.status === 'confirmed' ? 'green' : 'slate'}>{p.status}</Badge></td></tr>
              ))}</tbody></table></TableWrap>
          )}
        </Card>
      </div>
    </Shell>
  );
}
