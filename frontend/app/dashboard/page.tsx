'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, CartesianGrid } from 'recharts';
import { api } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Card, Empty, PageTitle, SectionTitle, Select, Stat } from '@/components/ui';

const PRESETS = [
  { v: 'today', l: 'Today' },
  { v: 'week', l: 'Last 7 days' },
  { v: 'month', l: 'Last 30 days' },
  { v: 'year', l: 'Last 12 months' },
  { v: 'all', l: 'All time' },
];

export default function Dashboard() {
  const [preset, setPreset] = useState('month');
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', preset],
    queryFn: async () => (await api.get(`/dashboard?preset=${preset}`)).data,
  });
  const insights = useQuery({
    queryKey: ['insights', preset],
    queryFn: async () => (await api.get(`/ai/insights?preset=${preset}`)).data,
  });

  return (
    <Shell>
      <PageTitle title="Good day — here&apos;s your business at a glance" sub="Sales, profit, stock and smart highlights for the selected period."
        right={<Select value={preset} onChange={(e) => setPreset(e.target.value)} className="!w-40">
          {PRESETS.map((p) => <option key={p.v} value={p.v}>{p.l}</option>)}
        </Select>} />
      {isLoading ? (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">{[0, 1, 2, 3].map((i) => <Card key={i}><div className="h-16 animate-pulse rounded-xl bg-slate-100" /></Card>)}</div>
      ) : error ? (
        <Empty title="Couldn&apos;t load the dashboard" sub="Please check your connection and try again." />
      ) : data && (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Stat accent="emerald" label="Revenue" value={fmt(data.revenue)} sub={`${data.orders ?? 0} orders`} />
            <Stat accent="teal" label="Gross profit" value={fmt(data.gross_profit)} sub={`Margin ${margin(data.gross_profit, data.revenue)}`} />
            <Stat accent="indigo" label="Net profit" value={fmt(data.net_profit)} sub={`After ${fmt(data.expenses)} expenses`} />
            <Stat accent={((data.low_stock_count ?? 0) > 0 || (data.out_of_stock_count ?? 0) > 0) ? 'amber' : 'emerald'} label="Stock health" value={`${data.inventory?.units ?? 0} units`} sub={`${data.low_stock_count ?? 0} low · ${data.out_of_stock_count ?? 0} out`} />
          </div>
          <div className="mt-4 grid gap-4 lg:grid-cols-5">
            <Card className="lg:col-span-3">
              <SectionTitle title="Sales trend" sub="Revenue across the selected period" />
              <div style={{ height: 260 }}>
                <ResponsiveContainer>
                  <LineChart data={data.sales_trend || []} margin={{ left: -12, right: 8, top: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                    <XAxis dataKey="period" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                    <Tooltip />
                    <Line type="monotone" dataKey="revenue" stroke="#059669" strokeWidth={2.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card className="lg:col-span-2">
              <SectionTitle title="Bestsellers" sub="Top products by quantity sold" />
              <div style={{ height: 220 }}>
                <ResponsiveContainer>
                  <BarChart data={(data.top_products || []).slice(0, 6)} layout="vertical" margin={{ left: 8, right: 16 }}>
                    <XAxis type="number" hide />
                    <YAxis type="category" dataKey="product_name" width={110} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                    <Tooltip />
                    <Bar dataKey="quantity" fill="#10b981" radius={[0, 8, 8, 0]} barSize={14} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <ul className="mt-2 divide-y divide-slate-100 text-sm">
                {(data.top_products || []).slice(0, 5).map((t: any) => (
                  <li key={t.product_id} className="flex items-center justify-between py-2">
                    <span className="font-medium">{t.product_name}</span>
                    <span className="text-slate-500">{t.quantity} sold · {fmt(t.revenue)}</span>
                  </li>
                ))}
                {!(data.top_products || []).length && <li className="py-3 text-sm text-slate-500">No sales yet in this period.</li>}
              </ul>
            </Card>
          </div>
          <Card className="mt-4 border-emerald-100 bg-gradient-to-br from-emerald-50/70 to-teal-50/40">
            <SectionTitle title="Highlights for you" sub="Automatically spotted from sales, stock and expenses" />
            {(insights.data?.insights || []).length ? (
              <div className="grid gap-2.5 md:grid-cols-2">
                {(insights.data.insights || []).slice(0, 4).map((i: any, idx: number) => (
                  <div key={idx} className="rounded-xl border border-white/60 bg-white/80 p-3.5">
                    <div className="text-sm font-bold">{i.title}</div>
                    <div className="mt-0.5 text-[13px] leading-relaxed text-slate-500">{i.detail}</div>
                  </div>
                ))}
              </div>
            ) : <div className="text-sm text-slate-500">Everything looks steady. New highlights will appear here.</div>}
          </Card>
        </>
      )}
    </Shell>
  );
}

function fmt(n: any) {
  const v = Number(n ?? 0);
  return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
function margin(profit: any, revenue: any) {
  const r = Number(revenue || 0);
  if (!r) return '—';
  return `${((Number(profit || 0) / r) * 100).toFixed(1)}%`;
}
