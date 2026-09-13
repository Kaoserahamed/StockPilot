'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Badge, Btn, Card, Empty, Field, Input, PageTitle, TableWrap } from '@/components/ui';

export default function ProductsPage() {
  const [q, setQ] = useState('');
  const [form, setForm] = useState({ name: '', sku: '', selling_price: '', purchase_price: '', category_id: '', brand: '', min_stock: '5' });
  const [msg, setMsg] = useState('');
  const cats = useQuery({ queryKey: ['cats'], queryFn: async () => (await api.get('/categories')).data });
  const list = useQuery({ queryKey: ['products', q], queryFn: async () => (await api.get(`/products${q ? `?q=${encodeURIComponent(q)}` : ''}`)).data });
  const set = (k: string, v: string) => setForm((s) => ({ ...s, [k]: v }));

  const create = async () => {
    setMsg('');
    try {
      await api.post('/products', {
        name: form.name, sku: form.sku,
        selling_price: Number(form.selling_price || 0), purchase_price: Number(form.purchase_price || 0),
        category_id: form.category_id ? Number(form.category_id) : null,
        brand: form.brand || null, min_stock: Number(form.min_stock || 0),
      });
      setForm({ name: '', sku: '', selling_price: '', purchase_price: '', category_id: '', brand: '', min_stock: '5' });
      list.refetch(); setMsg('Product created.');
    } catch (e) { setMsg(errMsg(e)); }
  };
  const deactivate = async (id: number) => { try { await api.post(`/products/${id}/deactivate`); list.refetch(); } catch (e) { setMsg(errMsg(e)); } };
  const activate = async (id: number) => { try { await api.post(`/products/${id}/activate`); list.refetch(); } catch (e) { setMsg(errMsg(e)); } };

  return (
    <Shell>
      <PageTitle title="Products" sub="Catalog, pricing and stock levels." />
      {msg && <div className="mb-3 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h3 className="font-bold">New product</h3>
          <div className="mt-3 space-y-2.5">
            <Field label="Name"><Input value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="Rice 1kg" /></Field>
            <Field label="SKU"><Input value={form.sku} onChange={(e) => set('sku', e.target.value)} placeholder="RICE-001" /></Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Sell price"><Input value={form.selling_price} onChange={(e) => set('selling_price', e.target.value)} placeholder="85" /></Field>
              <Field label="Cost price"><Input value={form.purchase_price} onChange={(e) => set('purchase_price', e.target.value)} placeholder="65" /></Field>
            </div>
            <Field label="Category"><select value={form.category_id} onChange={(e) => set('category_id', e.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"><option value="">No category</option>{(cats.data || []).map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
            <div className="grid grid-cols-2 gap-2">
              <Field label="Brand"><Input value={form.brand} onChange={(e) => set('brand', e.target.value)} /></Field>
              <Field label="Min stock"><Input value={form.min_stock} onChange={(e) => set('min_stock', e.target.value)} /></Field>
            </div>
            <Btn onClick={create} disabled={!form.name || !form.sku} className="w-full">Add product</Btn>
          </div>
        </Card>
        <div className="lg:col-span-2">
          <Card>
            <div className="mb-3 flex gap-2"><Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name, SKU, barcode, brand…" /></div>
            {list.isLoading ? <div className="h-24 animate-pulse rounded-xl bg-slate-100" /> : !(list.data || []).length ? <Empty title="No products yet" sub="Add your first product." /> : (
              <TableWrap><table className="w-full text-sm"><thead><tr className="bg-slate-50 text-left text-xs text-slate-500"><th className="px-3 py-2">Name</th><th className="px-3 py-2">SKU</th><th className="px-3 py-2">Price</th><th className="px-3 py-2">Stock</th><th className="px-3 py-2">Status</th><th className="px-3 py-2"></th></tr></thead>
                <tbody>{(list.data || []).map((p: any) => (
                  <tr key={p.id} className="border-t border-slate-100"><td className="px-3 py-2 font-medium">{p.name}</td><td className="px-3 py-2 text-slate-500">{p.sku}</td><td className="px-3 py-2">{p.selling_price}</td><td className="px-3 py-2">{p.quantity_on_hand}</td><td className="px-3 py-2">{p.is_active ? <Badge tone="green">active</Badge> : <Badge>off</Badge>}</td><td className="px-3 py-2 text-right">{p.is_active
                    ? <button onClick={() => deactivate(p.id)} className="text-xs font-semibold text-rose-700 hover:underline">Deactivate</button>
                    : <button onClick={() => activate(p.id)} className="text-xs font-semibold text-emerald-700 hover:underline">Activate</button>}</td></tr>
                ))}</tbody></table></TableWrap>
            )}
          </Card>
        </div>
      </div>
    </Shell>
  );
}
