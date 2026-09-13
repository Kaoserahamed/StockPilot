'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, downloadBlob, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Badge, Btn, Card, Empty, Field, Input, PageTitle, TableWrap } from '@/components/ui';

export default function SalesPage() {
  const [saleId, setSaleId] = useState('');
  const [ret, setRet] = useState({ item: '', qty: '', reason: 'Customer return' });
  const [msg, setMsg] = useState('');
  const list = useQuery({ queryKey: ['sales'], queryFn: async () => (await api.get('/sales')).data });

  const doReturn = async () => {
    setMsg('');
    try {
      const r = await api.post('/returns', { sale_id: Number(saleId), reason: ret.reason, items: [{ sale_item_id: Number(ret.item), quantity: Number(ret.qty) }] });
      setMsg(`Return recorded · refund ${r.data.refund_amount}.`); list.refetch();
    } catch (e) { setMsg(errMsg(e)); }
  };

  return (
    <Shell>
      <PageTitle title="Sales & Returns" sub="History, invoices and item returns." />
      {msg && <div className="mb-3 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h3 className="font-bold">Record a return</h3>
          <div className="mt-3 space-y-2.5">
            <Field label="Sale ID"><Input value={saleId} onChange={(e) => setSaleId(e.target.value)} placeholder="e.g. 12" /></Field>
            <Field label="Sale item ID"><Input value={ret.item} onChange={(e) => setRet({ ...ret, item: e.target.value })} placeholder="from sale details" /></Field>
            <Field label="Qty"><Input value={ret.qty} onChange={(e) => setRet({ ...ret, qty: e.target.value })} placeholder="1" /></Field>
            <Field label="Reason"><Input value={ret.reason} onChange={(e) => setRet({ ...ret, reason: e.target.value })} /></Field>
            <Btn onClick={doReturn} disabled={!saleId || !ret.item || !ret.qty} className="w-full">Submit return</Btn>
          </div>
        </Card>
        <Card className="lg:col-span-2">
          {list.isLoading ? <div className="h-24 animate-pulse rounded-xl bg-slate-100" /> : !(list.data || []).length ? <Empty title="No sales yet" /> : (
            <TableWrap><table className="w-full text-sm"><thead><tr className="bg-slate-50 text-left text-xs text-slate-500"><th className="px-3 py-2">Invoice</th><th className="px-3 py-2">Total</th><th className="px-3 py-2">Status</th><th className="px-3 py-2"></th></tr></thead>
              <tbody>{(list.data || []).map((s: any) => (
                <tr key={s.id} className="border-t border-slate-100"><td className="px-3 py-2 font-medium">{s.invoice_no} <span className="text-slate-400">#{s.id}</span></td><td className="px-3 py-2">{s.total_amount}</td><td className="px-3 py-2"><Badge tone={s.status === 'completed' ? 'green' : 'amber'}>{s.status}</Badge></td>
                  <td className="px-3 py-2 text-right"><button onClick={() => downloadBlob(`/invoices/${s.id}/pdf`, `${s.invoice_no}.pdf`)} className="text-xs font-semibold text-emerald-700 hover:underline">PDF</button></td></tr>
              ))}</tbody></table></TableWrap>
          )}
        </Card>
      </div>
    </Shell>
  );
}
