'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Badge, Btn, Card, Empty, Field, Input, PageTitle, TableWrap } from '@/components/ui';

export default function PartiesPage() {
  const [tab, setTab] = useState<'customers' | 'suppliers'>('customers');
  const [c, setC] = useState({ name: '', phone: '' });
  const [s, setS] = useState({ company_name: '', phone: '' });
  const [msg, setMsg] = useState('');
  const custs = useQuery({ queryKey: ['custs'], queryFn: async () => (await api.get('/customers')).data });
  const sups = useQuery({ queryKey: ['sups'], queryFn: async () => (await api.get('/suppliers')).data });

  return (
    <Shell>
      <PageTitle title="Contacts" sub="Customers and suppliers in one place."
        right={<div className="flex gap-2"><Btn variant={tab === 'customers' ? 'primary' : 'secondary'} onClick={() => setTab('customers')}>Customers</Btn><Btn variant={tab === 'suppliers' ? 'primary' : 'secondary'} onClick={() => setTab('suppliers')}>Suppliers</Btn></div>} />
      {msg && <div className="mb-3 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      {tab === 'customers' ? (
        <div className="grid gap-4 lg:grid-cols-3">
          <Card>
            <h3 className="font-bold">New customer</h3>
            <div className="mt-3 space-y-2.5">
              <Field label="Name"><Input value={c.name} onChange={(e) => setC({ ...c, name: e.target.value })} /></Field>
              <Field label="Phone"><Input value={c.phone} onChange={(e) => setC({ ...c, phone: e.target.value })} /></Field>
              <Btn className="w-full" disabled={!c.name} onClick={async () => { try { await api.post('/customers', c); setC({ name: '', phone: '' }); custs.refetch(); setMsg('Customer added.'); } catch (e) { setMsg(errMsg(e)); } }}>Add</Btn>
            </div>
          </Card>
          <Card className="lg:col-span-2">
            {(custs.data || []).length ? <TableWrap><table className="w-full text-sm"><thead><tr className="bg-slate-50 text-left text-xs text-slate-500"><th className="px-3 py-2">Name</th><th className="px-3 py-2">Phone</th><th className="px-3 py-2">Due</th></tr></thead><tbody>{(custs.data || []).map((x: any) => <tr key={x.id} className="border-t border-slate-100"><td className="px-3 py-2 font-medium">{x.name}</td><td className="px-3 py-2">{x.phone || '—'}</td><td className="px-3 py-2">{x.outstanding_balance}</td></tr>)}</tbody></table></TableWrap> : <Empty title="No customers yet" />}
          </Card>
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          <Card>
            <h3 className="font-bold">New supplier</h3>
            <div className="mt-3 space-y-2.5">
              <Field label="Company"><Input value={s.company_name} onChange={(e) => setS({ ...s, company_name: e.target.value })} /></Field>
              <Field label="Phone"><Input value={s.phone} onChange={(e) => setS({ ...s, phone: e.target.value })} /></Field>
              <Btn className="w-full" disabled={!s.company_name} onClick={async () => { try { await api.post('/suppliers', s); setS({ company_name: '', phone: '' }); sups.refetch(); setMsg('Supplier added.'); } catch (e) { setMsg(errMsg(e)); } }}>Add</Btn>
            </div>
          </Card>
          <Card className="lg:col-span-2">
            {(sups.data || []).length ? <TableWrap><table className="w-full text-sm"><thead><tr className="bg-slate-50 text-left text-xs text-slate-500"><th className="px-3 py-2">Company</th><th className="px-3 py-2">Phone</th><th className="px-3 py-2">Due</th></tr></thead><tbody>{(sups.data || []).map((x: any) => <tr key={x.id} className="border-t border-slate-100"><td className="px-3 py-2 font-medium">{x.company_name}</td><td className="px-3 py-2">{x.phone || '—'}</td><td className="px-3 py-2">{x.outstanding_balance}</td></tr>)}</tbody></table></TableWrap> : <Empty title="No suppliers yet" />}
          </Card>
        </div>
      )}
      <div className="mt-2 text-xs text-slate-400">Tip: open a contact to see purchase/sales history via the API (<Badge>GET /suppliers/:id/purchases</Badge> <Badge>GET /customers/:id/sales</Badge>).</div>
    </Shell>
  );
}
