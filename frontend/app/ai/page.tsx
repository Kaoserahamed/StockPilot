'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Badge, Btn, Card, Empty, Field, Input, PageTitle, Select, TableWrap } from '@/components/ui';

export default function AIPage() {
  const [q, setQ] = useState('');
  const [answer, setAnswer] = useState('');
  const [msg, setMsg] = useState('');
  const [preset, setPreset] = useState('month');
  const insights = useQuery({ queryKey: ['ai-ins', preset], queryFn: async () => (await api.get(`/ai/insights?preset=${preset}`)).data });
  const forecast = useQuery({ queryKey: ['ai-fc'], queryFn: async () => (await api.get('/ai/forecast?days=30')).data });
  const reorder = useQuery({ queryKey: ['ai-re'], queryFn: async () => (await api.get('/ai/reorder-recommendations?days=30')).data });
  const anomalies = useQuery({ queryKey: ['ai-an'], queryFn: async () => (await api.get('/ai/anomalies')).data });
  const recs = useQuery({ queryKey: ['ai-recs'], queryFn: async () => (await api.get('/ai/recommendations')).data });

  const ask = async () => {
    setMsg('');
    try { const r = await api.post('/ai/chat', { question: q, save: true }); setAnswer(r.data.answer); recs.refetch(); }
    catch (e) { setMsg(errMsg(e)); }
  };
  const mark = async (id: number, patch: any) => { try { await api.patch(`/ai/recommendations/${id}`, patch); recs.refetch(); } catch (e) { setMsg(errMsg(e)); } };

  return (
    <Shell>
      <PageTitle title="AI Assistant" sub="Insights, forecasts, reorders and Q&A over your live data."
        right={<Select value={preset} onChange={(e) => setPreset(e.target.value)} className="!w-36">{['today', 'week', 'month', 'year', 'all'].map((p) => <option key={p} value={p}>{p}</option>)}</Select>} />
      {msg && <div className="mb-3 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{msg}</div>}
      <Card>
        <h3 className="font-bold">Ask about your business</h3>
        <div className="mt-2 flex gap-2"><Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. Which products should I reorder this week?" /><Btn onClick={ask} disabled={!q}>Ask</Btn></div>
        {answer && <div className="mt-2 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-900">{answer}</div>}
      </Card>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <h3 className="font-bold">Insights</h3>
          <div className="mt-2 space-y-2">{(insights.data?.insights || []).map((i: any, k: number) => <div key={k} className="rounded-xl bg-slate-50 px-3 py-2 text-sm"><div className="font-bold">{i.title}</div><div className="text-slate-500">{i.detail}</div></div>)}
            {!(insights.data?.insights || []).length && <Empty title="No insights yet" />}</div>
        </Card>
        <Card>
          <h3 className="font-bold">Anomalies</h3>
          <div className="mt-2 space-y-2">{(anomalies.data?.anomalies || []).map((a: any, k: number) => <div key={k} className="rounded-xl bg-amber-50 px-3 py-2 text-sm"><div className="font-bold">{a.title}</div><div className="text-slate-600">{a.detail}</div></div>)}
            {!(anomalies.data?.anomalies || []).length && <div className="mt-2 text-sm text-slate-500">No anomalies detected.</div>}</div>
        </Card>
        <Card>
          <h3 className="font-bold">Reorder recommendations</h3>
          <div className="mt-2 max-h-72 overflow-auto">{(reorder.data?.recommendations || []).slice(0, 20).map((r: any) => <div key={r.product_id} className="flex items-center justify-between border-b border-slate-100 py-1.5 text-sm"><span className="font-medium">{r.product_name}</span><span>{r.needs_reorder ? <Badge tone="amber">order {r.recommended_qty}</Badge> : <Badge tone="green">ok</Badge>}</span></div>)}
            {!(reorder.data?.recommendations || []).length && <Empty title="No data" />}</div>
        </Card>
        <Card>
          <h3 className="font-bold">Demand forecast (30d)</h3>
          <div className="mt-2 max-h-72 overflow-auto">{(forecast.data?.products || []).slice(0, 20).map((r: any) => <div key={r.product_id} className="flex items-center justify-between border-b border-slate-100 py-1.5 text-sm"><span className="font-medium">{r.product_name}</span><span className="text-slate-500">{r.predicted_demand} units · stock {r.current_stock}</span></div>)}
            {!(forecast.data?.products || []).length && <Empty title="No data" />}</div>
        </Card>
      </div>
      <Card className="mt-4">
        <h3 className="font-bold">Recommendation history</h3>
        <div className="mt-2 space-y-2">{(recs.data || []).slice(0, 20).map((r: any) => (
          <div key={r.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm">
            <div><span className="font-bold">[{r.kind}] {r.title}</span><div className="text-slate-500">{String(r.body).slice(0, 160)}</div></div>
            <div className="flex gap-2">{!r.reviewed && <button onClick={() => mark(r.id, { reviewed: true })} className="text-xs font-semibold text-emerald-700 hover:underline">Mark reviewed</button>}{!r.acted_upon && <button onClick={() => mark(r.id, { acted_upon: true })} className="text-xs font-semibold text-emerald-700 hover:underline">Mark acted</button>}{r.reviewed && <Badge tone="green">reviewed</Badge>}{r.acted_upon && <Badge tone="blue">acted</Badge>}</div>
          </div>))}
          {!(recs.data || []).length && <Empty title="No saved recommendations yet" />}</div>
      </Card>
    </Shell>
  );
}
