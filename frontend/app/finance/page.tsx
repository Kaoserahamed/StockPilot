'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Card, Empty, PageTitle, Select, Stat } from '@/components/ui';

const PRESETS = [{ v: 'today', l: 'Today' }, { v: 'week', l: 'Last 7 days' }, { v: 'month', l: 'Last 30 days' }, { v: 'year', l: 'Last 12 months' }, { v: 'all', l: 'All time' }];

export default function FinancePage() {
  const [preset, setPreset] = useState('month');
  const rev = useQuery({ queryKey: ['rev', preset], queryFn: async () => (await api.get(`/finance/revenue?preset=${preset}`)).data });
  const cogs = useQuery({ queryKey: ['cogs', preset], queryFn: async () => (await api.get(`/finance/cogs?preset=${preset}`)).data });
  const profit = useQuery({ queryKey: ['profit', preset], queryFn: async () => (await api.get(`/finance/profit?preset=${preset}`)).data });

  return (
    <Shell>
      <PageTitle title="Finance" sub="Revenue, costs and profit for the selected period."
        right={<Select value={preset} onChange={(e) => setPreset(e.target.value)} className="!w-40">{PRESETS.map((p) => <option key={p.v} value={p.v}>{p.l}</option>)}</Select>} />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Gross revenue" value={rev.data?.gross_revenue ?? '—'} sub={`${rev.data?.orders ?? 0} orders`} />
        <Stat accent="indigo" label="Net revenue" value={rev.data?.net_revenue ?? '—'} sub={`Refunded ${rev.data?.refunded ?? 0}`} />
        <Stat accent="amber" label="COGS" value={cogs.data?.total_cogs ?? '—'} />
        <Stat accent="teal" label="Net profit" value={profit.data?.net_profit ?? '—'} sub={`Gross ${profit.data?.gross_profit ?? '—'}`} />
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <h3 className="font-bold">Revenue trend</h3>
          <div className="mt-2 space-y-1.5 text-sm">{(rev.data?.trend || []).slice(-10).map((t: any) => <div key={t.period} className="flex justify-between rounded-lg bg-slate-50 px-3 py-1.5"><span>{t.period}</span><span className="font-semibold">{t.revenue}</span></div>)}
            {!(rev.data?.trend || []).length && <Empty title="No revenue in period" />}</div>
        </Card>
        <Card>
          <h3 className="font-bold">Profit breakdown</h3>
          <div className="mt-2 space-y-1.5 text-sm">
            {profit.data ? Object.entries(profit.data).map(([k, v]) => <div key={k} className="flex justify-between rounded-lg bg-slate-50 px-3 py-1.5"><span className="text-slate-500">{k}</span><span className="font-semibold">{String(v)}</span></div>) : <Empty title="Loading…" />}
          </div>
        </Card>
      </div>
    </Shell>
  );
}
