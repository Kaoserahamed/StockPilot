'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Btn, Card, Empty, Field, Input, PageTitle, TableWrap } from '@/components/ui';

export default function PosPage() {
  const [q, setQ] = useState('');
  const [cart, setCart] = useState<any[]>([]);
  const [msg, setMsg] = useState('');
  const [paid, setPaid] = useState('');
  const search = useQuery({ queryKey: ['pos', q], queryFn: async () => (await api.get(`/pos/search?q=${encodeURIComponent(q || 'a')}`)).data, enabled: q.length >= 1 });

  const add = (p: any) => {
    setCart((c) => {
      const f = c.find((x) => x.product_id === p.id);
      if (f) return c.map((x) => x.product_id === p.id ? { ...x, quantity: x.quantity + 1 } : x);
      return [...c, { product_id: p.id, name: p.name, quantity: 1, unit_price: p.selling_price }];
    });
  };
  const total = cart.reduce((s, i) => s + i.quantity * (i.unit_price || 0), 0);

  const checkout = async () => {
    setMsg('');
    try {
      const r = await api.post('/sales/checkout', { items: cart.map((i) => ({ product_id: i.product_id, quantity: i.quantity, unit_price: i.unit_price })), paid_amount: paid ? Number(paid) : total, payment_method: 'cash' });
      setCart([]); setPaid('');
      setMsg(`Sale ${r.data.invoice_no} done · total ${r.data.total_amount}.`);
    } catch (e) { setMsg(errMsg(e)); }
  };

  return (
    <Shell>
      <PageTitle title="POS Terminal" sub="Search, add to cart and checkout in seconds." />
      {msg && <div className="mb-3 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <Field label="Search products (name / SKU / barcode)"><Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Type to search…" /></Field>
          <div className="mt-3 space-y-2">
            {(search.data || []).map((p: any) => (
              <div key={p.id} className="flex items-center justify-between rounded-xl border border-slate-100 px-3 py-2 text-sm">
                <div><div className="font-semibold">{p.name}</div><div className="text-xs text-slate-500">{p.sku} · stock {p.quantity} · {p.selling_price}</div></div>
                <Btn variant="secondary" onClick={() => add(p)}>Add</Btn>
              </div>
            ))}
            {q && !(search.data || []).length && !search.isLoading && <Empty title="No matches" sub="Try another name, SKU or barcode." />}
          </div>
        </Card>
        <Card className="lg:col-span-2">
          <h3 className="font-bold">Cart ({cart.length})</h3>
          <div className="mt-2 space-y-2">
            {cart.map((i) => (
              <div key={i.product_id} className="flex items-center justify-between text-sm">
                <span className="font-medium">{i.name} × {i.quantity}</span>
                <span className="flex items-center gap-2">{(i.quantity * i.unit_price).toFixed(2)}
                  <button onClick={() => setCart((c) => c.filter((x) => x.product_id !== i.product_id))} className="text-xs text-rose-600 hover:underline">remove</button></span>
              </div>
            ))}
            {!cart.length && <Empty title="Cart is empty" />}
          </div>
          {!!cart.length && (
            <div className="mt-3 space-y-2 border-t border-slate-100 pt-3">
              <div className="flex justify-between text-sm font-bold"><span>Total</span><span>{total.toFixed(2)}</span></div>
              <Field label="Paid amount (default: full)"><Input value={paid} onChange={(e) => setPaid(e.target.value)} placeholder={String(total.toFixed(2))} /></Field>
              <Btn className="w-full" onClick={checkout}>Checkout</Btn>
            </div>
          )}
        </Card>
      </div>
    </Shell>
  );
}
