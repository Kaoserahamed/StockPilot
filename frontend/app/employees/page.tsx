'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, errMsg } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Badge, Btn, Card, Empty, Field, Input, PageTitle, TableWrap } from '@/components/ui';

export default function EmployeesPage() {
  const [f, setF] = useState({ name: '', email: '', password: '', role: 'Cashier' });
  const [msg, setMsg] = useState('');
  const list = useQuery({ queryKey: ['emp'], queryFn: async () => (await api.get('/employees')).data });
  const set = (k: string, v: string) => setF((s) => ({ ...s, [k]: v }));

  const create = async () => {
    setMsg('');
    try { await api.post('/employees', f); setF({ name: '', email: '', password: '', role: 'Cashier' }); list.refetch(); setMsg('Team member added.'); }
    catch (e) { setMsg(errMsg(e)); }
  };
  const act = async (id: number, op: string, body?: any) => {
    try {
      if (op === 'delete') await api.delete(`/employees/${id}`);
      else if (op === 'role') await api.patch(`/employees/${id}/role`, body);
      else await api.post(`/employees/${id}/${op}`, body || {});
      list.refetch();
    } catch (e) { setMsg(errMsg(e)); }
  };

  return (
    <Shell>
      <PageTitle title="Team" sub="Employees, roles and access." />
      {msg && <div className="mb-3 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{msg}</div>}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h3 className="font-bold">Invite member</h3>
          <div className="mt-3 space-y-2.5">
            <Field label="Name"><Input value={f.name} onChange={(e) => set('name', e.target.value)} /></Field>
            <Field label="Email"><Input value={f.email} onChange={(e) => set('email', e.target.value)} /></Field>
            <Field label="Password"><Input type="password" value={f.password} onChange={(e) => set('password', e.target.value)} /></Field>
            <Field label="Role"><select value={f.role} onChange={(e) => set('role', e.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm">{['Owner', 'Manager', 'Cashier'].map((r) => <option key={r} value={r}>{r}</option>)}</select></Field>
            <Btn onClick={create} disabled={!f.name || !f.password} className="w-full">Add member</Btn>
          </div>
        </Card>
        <Card className="lg:col-span-2">
          {(list.data || []).length ? <TableWrap><table className="w-full text-sm"><thead><tr className="bg-slate-50 text-left text-xs text-slate-500"><th className="px-3 py-2">Name</th><th className="px-3 py-2">Role</th><th className="px-3 py-2">Status</th><th className="px-3 py-2"></th></tr></thead>
            <tbody>{(list.data || []).map((m: any) => (
              <tr key={m.membership_id} className="border-t border-slate-100"><td className="px-3 py-2 font-medium">{m.user?.name}</td><td className="px-3 py-2"><Badge tone="blue">{m.role}</Badge></td><td className="px-3 py-2">{m.is_active ? <Badge tone="green">active</Badge> : <Badge>off</Badge>}</td>
                <td className="px-3 py-2 text-right space-x-2 text-xs font-semibold">
                  {m.is_active ? <button onClick={() => act(m.membership_id, 'deactivate')} className="text-amber-700 hover:underline">Deactivate</button> : <button onClick={() => act(m.membership_id, 'activate')} className="text-emerald-700 hover:underline">Activate</button>}
                  <button onClick={() => { const r = prompt('New role (Owner/Manager/Cashier):', m.role); if (r) act(m.membership_id, 'role', { role: r }); }} className="text-slate-600 hover:underline">Role</button>
                  <button onClick={() => { if (confirm('Remove member?')) act(m.membership_id, 'delete'); }} className="text-rose-700 hover:underline">Remove</button>
                </td></tr>))}</tbody></table></TableWrap> : <Empty title="No team members" />}
        </Card>
      </div>
    </Shell>
  );
}
