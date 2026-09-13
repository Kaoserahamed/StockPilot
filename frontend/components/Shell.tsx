'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { ErrorBoundary } from '@/components/ErrorBoundary';

const GROUPS: { title: string; links: { href: string; label: string; icon: string }[] }[] = [
  {
    title: 'Sell',
    links: [
      { href: '/dashboard', label: 'Dashboard', icon: '◧' },
      { href: '/pos', label: 'POS Terminal', icon: '◈' },
      { href: '/sales', label: 'Sales & Returns', icon: '◎' },
      { href: '/purchases', label: 'Purchases', icon: '⬣' },
    ],
  },
  {
    title: 'Manage',
    links: [
      { href: '/inventory', label: 'Inventory', icon: '▦' },
      { href: '/products', label: 'Products', icon: '⬢' },
      { href: '/categories', label: 'Categories', icon: '▤' },
      { href: '/parties', label: 'Contacts', icon: '◐' },
      { href: '/expenses', label: 'Expenses', icon: '⬔' },
    ],
  },
  {
    title: 'Grow',
    links: [
      { href: '/finance', label: 'Finance', icon: '⬥' },
      { href: '/reports', label: 'Reports', icon: '▨' },
      { href: '/ai', label: 'AI Assistant', icon: '✦' },
    ],
  },
  {
    title: 'Workspace',
    links: [
      { href: '/employees', label: 'Team', icon: '◍' },
      { href: '/audit', label: 'Activity Log', icon: '≣' },
      { href: '/settings', label: 'Settings', icon: '⚙' },
      { href: '/subscription', label: 'Billing', icon: '⬓' },
    ],
  },
];

function isActive(path: string, href: string) {
  return path === href || path.startsWith(href + '/');
}

export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const { user, logout } = useAuth();
  const biz = useQuery({ queryKey: ['biz'], queryFn: async () => (await api.get('/businesses/me')).data });

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col bg-slate-950 p-4 text-slate-200 md:flex">
        <div className="flex items-center gap-2.5 px-1 pb-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 text-lg font-black text-white">S</div>
          <div>
            <div className="text-[15px] font-extrabold tracking-tight text-white">StockPilot</div>
            <div className="max-w-[160px] truncate text-[11px] text-slate-400">{biz.data?.name || 'Your business'}</div>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-4 overflow-auto pr-1">
          {GROUPS.map((g) => (
            <div key={g.title}>
              <div className="px-2 pb-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">{g.title}</div>
              <div className="space-y-0.5">
                {g.links.map((l) => {
                  const active = isActive(path, l.href);
                  return (
                    <Link key={l.href} href={l.href}
                      className={`flex items-center gap-2.5 rounded-xl px-3 py-2 text-[13.5px] font-medium transition ${active ? 'bg-emerald-500/15 text-white shadow-[inset_0_0_0_1px_rgba(16,185,129,0.35)]' : 'text-slate-300 hover:bg-white/5 hover:text-white'}`}>
                      <span className={`flex h-6 w-6 items-center justify-center rounded-lg text-[13px] ${active ? 'bg-emerald-500 text-white' : 'bg-white/10'}`}>{l.icon}</span>
                      {l.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
        <div className="mt-3 rounded-xl bg-white/5 p-3">
          <div className="truncate text-[13px] font-semibold text-white">{user?.name || 'Account'}</div>
          <div className="truncate text-[11px] text-slate-400">{user?.email || user?.phone || ''}</div>
          <button onClick={logout} className="mt-2 w-full rounded-lg bg-white/10 px-3 py-1.5 text-xs font-semibold hover:bg-white/15">Sign out</button>
        </div>
      </aside>
      <div className="min-w-0 flex-1">
        <div className="sticky top-0 z-10 border-b border-slate-200/70 bg-white/85 backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center gap-2 overflow-x-auto p-2 md:hidden">
            {GROUPS.flatMap((g) => g.links).map((l) => (
              <Link key={l.href} href={l.href} className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-semibold ${isActive(path, l.href) ? 'bg-emerald-600 text-white' : 'bg-slate-100'}`}>{l.label}</Link>
            ))}
          </div>
          <div className="mx-auto hidden max-w-6xl items-center justify-between px-4 py-2.5 md:flex">
            <div className="text-sm font-semibold text-slate-700">{biz.data?.name || 'Workspace'}</div>
            <div className="text-xs text-slate-500">Signed in as <span className="font-semibold text-slate-700">{user?.name || ''}</span></div>
          </div>
        </div>
        <main className="mx-auto max-w-6xl p-4 md:p-6">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
