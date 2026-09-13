'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Badge, Btn, Card, Empty, Field, Input, PageTitle, TableWrap } from '@/components/ui';

export default function InventoryPage() {
  const [form, setForm] = useState({ product_id: '', qty: '', sell: '', cost: '', reason: 'Manual adjustment' });
  const [msg, setMsg] = useState('');
  const over = useQuery({ queryKey: ['inv'], queryFn: async () => (await api.get('/inventory/overview')).data });
  const txs = useQuery({ queryKey: ['inv-tx'], queryFn: async () => (await api.get('/inventory/transactions')).data });
  const padj = useQuery({ queryKey: ['inv-price'], queryFn: async () => (await api.get('/inventory/price-adjustments')).data });
  const cur = (over.data || []).find((r: any) => String(r.id) === form.product_id);
  const set = (k: string, v: string) => setForm((s) => ({ ...s, [k]: v }));

  const apply = async () => {
    setMsg('');
    const hasQty = form.qty !== '';
    const hasPrice = form.sell !== '' || form.cost !== '';
    if (!form.product_id || !form.reason || (!hasQty && !hasPrice)) return;
    try {
      if (hasQty) {
        await api.post('/inventory/adjust', {
          product_id: Number(form.product_id), quantity_change: Number(form.qty), reason: form.reason,
        });
      }
      if (hasPrice) {
        await api.post('/inventory/adjust-price', {
          product_id: Number(form.product_id),
          new_selling_price: form.sell === '' ? null : Number(form.sell),
          new_purchase_price: form.cost === '' ? null : Number(form.cost),
          reason: form.reason,
        });
      }
      setForm({ ...form, qty: '', sell: '', cost: '' });
      over.refetch(); txs.refetch(); padj.refetch();
      setMsg('Adjustment applied.');
    } catch (e) { setMsg(errMsg(e)); }
  };

  return (
    <Shell>
      <PageTitle title="Inventory" sub="Live stock, adjustments, price changes and history." />
      {msg && <div className="mb-3 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h3 className="font-bold">Stock &amp; price adjustment</h3>
          <div className="mt-3 space-y-2.5">
            <Field label="Product ID">
              <Input value={form.product_id} onChange={(e) => set('product_id', e.target.value)} placeholder="e.g. 1" />
            </Field>
            <Field label="Qty change (+/-)"><Input value={form.qty} onChange={(e) => set('qty', e.target.value)} placeholder="e.g. -2 or 10" /></Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label="New sell price"><Input value={form.sell} onChange={(e) => set('sell', e.target.value)} placeholder={cur ? String(cur.selling_price ?? '') : 'optional'} /></Field>
              <Field label="New cost price"><Input value={form.cost} onChange={(e) => set('cost', e.target.value)} placeholder={cur ? String(cur.purchase_price ?? '') : 'optional'} /></Field>
            </div>
            <Field label="Reason"><Input value={form.reason} onChange={(e) => set('reason', e.target.value)} /></Field>
            <Btn onClick={apply}
              disabled={!form.product_id || !form.reason || (form.qty === '' && form.sell === '' && form.cost === '')}
              className="w-full">Apply</Btn>
            {cur && (
              <div className="rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-600">
                Current: qty <b>{cur.quantity}</b> · sell <b>{cur.selling_price}</b> · cost <b>{cur.purchase_price}</b>
              </div>
            )}
          </div>

          <h3 className="mt-5 font-bold">Recent price changes</h3>
          <div className="mt-2 max-h-48 space-y-1.5 overflow-auto text-xs text-slate-600">
            {(padj.data || []).slice(0, 20).map((p: any) => (
              <div key={p.id} className="rounded-lg bg-slate-50 px-2 py-1.5">
                product {p.product_id} · sell {p.old_selling_price} → <b>{p.new_selling_price}</b>
                {p.old_purchase_price !== p.new_purchase_price && <> · cost {p.old_purchase_price} → <b>{p.new_purchase_price}</b></>}
                <div className="text-[11px] text-slate-400">{p.reason}</div>
              </div>
            ))}
            {!(padj.data || []).length && <Empty title="No price changes yet" />}
          </div>
        </Card>
        <Card className="lg:col-span-2">
          <h3 className="font-bold">Stock overview</h3>
          <div className="mt-2">
            {over.isLoading ? <div className="h-24 animate-pulse rounded-xl bg-slate-100" /> : !(over.data || []).length ? <Empty title="No inventory rows" /> : (
              <TableWrap><table className="w-full text-sm"><thead><tr className="bg-slate-50 text-left text-xs text-slate-500"><th className="px-3 py-2">ID</th><th className="px-3 py-2">Product</th><th className="px-3 py-2">Qty</th><th className="px-3 py-2">Sell</th><th className="px-3 py-2">Cost</th><th className="px-3 py-2">Condition</th></tr></thead>
                <tbody>{(over.data || []).map((r: any) => (
                  <tr key={r.id} className="border-t border-slate-100"><td className="px-3 py-2">{r.id}</td><td className="px-3 py-2 font-medium">{r.name}</td><td className="px-3 py-2">{r.quantity}</td><td className="px-3 py-2">{r.selling_price}</td><td className="px-3 py-2">{r.purchase_price}</td><td className="px-3 py-2">{r.condition === 'ok' ? <Badge tone="green">ok</Badge> : r.condition === 'low' ? <Badge tone="amber">low</Badge> : <Badge tone="red">out</Badge>}</td></tr>
                ))}</tbody></table></TableWrap>
            )}
          </div>
          <h3 className="mt-5 font-bold">Recent movements</h3>
          <div className="mt-2 max-h-64 space-y-1.5 overflow-auto text-xs text-slate-600">
            {(txs.data || []).slice(0, 30).map((t: any) => <div key={t.id} className="rounded-lg bg-slate-50 px-2 py-1.5">#{t.id} · product {t.product_id} · {t.quantity_change > 0 ? '+' : ''}{t.quantity_change} · {t.tx_type}</div>)}
            {!(txs.data || []).length && <Empty title="No movements yet" />}
          </div>
        </Card>
      </div>
    </Shell>
  );
}
