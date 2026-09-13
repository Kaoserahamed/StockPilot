'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Btn, Card, Empty, Field, Input, PageTitle, TableWrap } from '@/components/ui';

export default function ExpensesPage() {
  const [form, setForm] = useState({ category: 'rent', amount: '', description: '' });
  const [msg, setMsg] = useState('');
  const list = useQuery({ queryKey: ['exp'], queryFn: async () => (await api.get('/expenses')).data });

  const create = async () => {
    setMsg('');
    try { await api.post('/expenses', { category: form.category, amount: Number(form.amount), description: form.description || null }); setForm({ ...form, amount: '', description: '' }); list.refetch(); setMsg('Expense recorded.'); }
    catch (e) { setMsg(errMsg(e)); }
  };

  return (
    <Shell>
      <PageTitle title="Expenses" sub="Rent, salaries, utilities and more." />
      {msg && <div className="mb-3 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h3 className="font-bold">New expense</h3>
          <div className="mt-3 space-y-2.5">
            <Field label="Category"><select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm">{['rent', 'salary', 'electricity', 'transport', 'maintenance', 'miscellaneous', 'other'].map((c) => <option key={c} value={c}>{c}</option>)}</select></Field>
            <Field label="Amount"><Input value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="1500" /></Field>
            <Field label="Note"><Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Optional" /></Field>
            <Btn onClick={create} disabled={!form.amount} className="w-full">Save expense</Btn>
          </div>
        </Card>
        <Card className="lg:col-span-2">
          {(list.data || []).length ? <TableWrap><table className="w-full text-sm"><thead><tr className="bg-slate-50 text-left text-xs text-slate-500"><th className="px-3 py-2">Category</th><th className="px-3 py-2">Amount</th><th className="px-3 py-2">Date</th><th className="px-3 py-2"></th></tr></thead><tbody>{(list.data || []).map((e: any) => <tr key={e.id} className="border-t border-slate-100"><td className="px-3 py-2 font-medium">{e.category}</td><td className="px-3 py-2">{e.amount}</td><td className="px-3 py-2 text-slate-500">{String(e.expense_date).slice(0, 10)}</td><td className="px-3 py-2 text-right"><button onClick={async () => { await api.delete(`/expenses/${e.id}`); list.refetch(); }} className="text-xs font-semibold text-rose-700 hover:underline">Delete</button></td></tr>)}</tbody></table></TableWrap> : <Empty title="No expenses yet" />}
        </Card>
      </div>
    </Shell>
  );
}
