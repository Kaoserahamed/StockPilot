'use client';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Shell } from '@/components/Shell';
import { Card, Empty, PageTitle, TableWrap } from '@/components/ui';

export default function AuditPage() {
  const list = useQuery({ queryKey: ['audit'], queryFn: async () => (await api.get('/audit-logs')).data });

  return (
    <Shell>
      <PageTitle title="Activity Log" sub="Who changed what, and when." />
      <Card>
        {list.isLoading ? <div className="h-24 animate-pulse rounded-xl bg-slate-100" /> : !(list.data || []).length ? <Empty title="No activity yet" /> : (
          <TableWrap><table className="w-full text-sm"><thead><tr className="bg-slate-50 text-left text-xs text-slate-500"><th className="px-3 py-2">ID</th><th className="px-3 py-2">Action</th><th className="px-3 py-2">Resource</th><th className="px-3 py-2">User</th><th className="px-3 py-2">At</th></tr></thead>
            <tbody>{(list.data || []).map((a: any) => <tr key={a.id} className="border-t border-slate-100"><td className="px-3 py-2">#{a.id}</td><td className="px-3 py-2 font-medium">{a.action}</td><td className="px-3 py-2 text-slate-500">{a.resource} {a.resource_id || ''}</td><td className="px-3 py-2">{a.user_id}</td><td className="px-3 py-2 text-slate-500">{String(a.created_at).slice(0, 19).replace('T', ' ')}</td></tr>)}</tbody></table></TableWrap>
        )}
      </Card>
    </Shell>
  );
}
