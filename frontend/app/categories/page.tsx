'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Badge, Btn, Card, Empty, Field, Input, PageTitle, TableWrap } from '@/components/ui';

export default function CategoriesPage() {
  const [name, setName] = useState('');
  const [msg, setMsg] = useState('');
  const list = useQuery({ queryKey: ['cats'], queryFn: async () => (await api.get('/categories')).data });

  const create = async () => {
    try { await api.post('/categories', { name }); setName(''); list.refetch(); setMsg('Category created.'); }
    catch (e) { setMsg(errMsg(e)); }
  };
  const deactivate = async (id: number) => { try { await api.post(`/categories/${id}/deactivate`); list.refetch(); } catch (e) { setMsg(errMsg(e)); } };

  return (
    <Shell>
      <PageTitle title="Categories" sub="Group products for faster search and reports." />
      {msg && <div className="mb-3 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h3 className="font-bold">New category</h3>
          <div className="mt-3 space-y-2.5">
            <Field label="Name"><Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Groceries" /></Field>
            <Btn onClick={create} disabled={!name} className="w-full">Add category</Btn>
          </div>
        </Card>
        <Card className="lg:col-span-2">
          {list.isLoading ? <div className="h-24 animate-pulse rounded-xl bg-slate-100" /> : !(list.data || []).length ? <Empty title="No categories yet" /> : (
            <TableWrap><table className="w-full text-sm"><thead><tr className="bg-slate-50 text-left text-xs text-slate-500"><th className="px-3 py-2">Name</th><th className="px-3 py-2">Status</th><th className="px-3 py-2"></th></tr></thead>
              <tbody>{(list.data || []).map((c: any) => (
                <tr key={c.id} className="border-t border-slate-100"><td className="px-3 py-2 font-medium">{c.name}</td><td className="px-3 py-2">{c.is_active ? <Badge tone="green">active</Badge> : <Badge>off</Badge>}</td><td className="px-3 py-2 text-right">{c.is_active && <button onClick={() => deactivate(c.id)} className="text-xs font-semibold text-rose-700 hover:underline">Deactivate</button>}</td></tr>
              ))}</tbody></table></TableWrap>
          )}
        </Card>
      </div>
    </Shell>
  );
}
