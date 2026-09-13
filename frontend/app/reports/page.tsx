'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, downloadBlob, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Btn, Card, Empty, PageTitle, Select, TableWrap } from '@/components/ui';

const KINDS = [{ v: 'sales', l: 'Sales' }, { v: 'inventory', l: 'Inventory' }, { v: 'purchases', l: 'Purchases' }, { v: 'expenses', l: 'Expenses' }, { v: 'profit', l: 'Profit' }];

export default function ReportsPage() {
  const [kind, setKind] = useState('sales');
  const [preset, setPreset] = useState('month');
  const [msg, setMsg] = useState('');
  const q = useQuery({ queryKey: ['rep', kind, preset], queryFn: async () => (await api.get(`/reports/${kind}?preset=${preset}`)).data });

  const dl = async (fmt: 'csv' | 'excel' | 'pdf') => {
    setMsg('');
    try { await downloadBlob(`/reports/${kind}?preset=${preset}&format=${fmt}`, `${kind}.${fmt === 'excel' ? 'xlsx' : fmt}`); }
    catch (e) { setMsg(errMsg(e)); }
  };

  const rows: any[] = q.data?.rows || (Array.isArray(q.data) ? q.data : []);
  const summary = q.data?.summary;

  return (
    <Shell>
      <PageTitle title="Reports" sub="Sales, inventory, purchases, expenses and profit — with exports."
        right={<><Select value={kind} onChange={(e) => setKind(e.target.value)} className="!w-36">{KINDS.map((k) => <option key={k.v} value={k.v}>{k.l}</option>)}</Select>
          <Select value={preset} onChange={(e) => setPreset(e.target.value)} className="!w-36">{['today', 'week', 'month', 'year', 'all'].map((p) => <option key={p} value={p}>{p}</option>)}</Select></>} />
      {msg && <div className="mb-3 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{msg}</div>}
      <Card>
        <div className="mb-3 flex flex-wrap gap-2">
          <Btn variant="secondary" onClick={() => dl('csv')}>Download CSV</Btn>
          <Btn variant="secondary" onClick={() => dl('excel')}>Download Excel</Btn>
          <Btn variant="secondary" onClick={() => dl('pdf')}>Download PDF</Btn>
        </div>
        {summary && <div className="mb-3 grid gap-2 sm:grid-cols-3">{Object.entries(summary).map(([k, v]) => <div key={k} className="rounded-xl bg-slate-50 px-3 py-2 text-sm"><div className="text-[11px] font-bold uppercase text-slate-500">{k}</div><div className="font-extrabold">{String(v)}</div></div>)}</div>}
        {q.isLoading ? <div className="h-24 animate-pulse rounded-xl bg-slate-100" /> : !rows.length && !summary ? <Empty title="No rows" /> : rows.length ? (
          <TableWrap><table className="w-full text-sm"><thead><tr className="bg-slate-50 text-left text-xs text-slate-500">{Object.keys(rows[0]).slice(0, 6).map((h) => <th key={h} className="px-3 py-2">{h}</th>)}</tr></thead>
            <tbody>{rows.slice(0, 50).map((r: any, i: number) => <tr key={i} className="border-t border-slate-100">{Object.keys(rows[0]).slice(0, 6).map((h) => <td key={h} className="px-3 py-2">{String(r[h])}</td>)}</tr>)}</tbody></table></TableWrap>
        ) : null}
      </Card>
    </Shell>
  );
}
