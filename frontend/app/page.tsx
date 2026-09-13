import Link from 'next/link';

const FEATURES = [
  { t: 'Fast POS checkout', d: 'Barcode search, discounts, tax and clean invoices in seconds.' },
  { t: 'Smart inventory', d: 'Live stock levels, low-stock alerts and adjustment history.' },
  { t: 'Purchases & suppliers', d: 'Track supplier orders, stock intake and pending payments.' },
  { t: 'Profit & finance', d: 'Revenue, costs, expenses and margins at a glance.' },
  { t: 'Reports & exports', d: 'Download sales, inventory and profit reports anytime.' },
  { t: 'AI assistant', d: 'Forecasts, reorder suggestions and business insights.' },
];

export default function Home() {
  return (
    <main className="min-h-screen">
      <div className="mx-auto max-w-6xl px-5 pb-16 pt-10">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-600 text-xl font-black text-white">S</div>
            <div className="text-lg font-extrabold tracking-tight">StockPilot</div>
          </div>
          <div className="flex gap-2">
            <Link href="/login" className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">Sign in</Link>
            <Link href="/register" className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">Get started</Link>
          </div>
        </header>

        <div className="mt-14 grid items-center gap-10 md:grid-cols-2">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">New · AI demand forecasting included</div>
            <h1 className="mt-4 text-4xl font-extrabold leading-[1.05] tracking-tight md:text-5xl">Run your shop with calm, clear numbers.</h1>
            <p className="mt-4 max-w-md text-[15px] leading-relaxed text-slate-600">StockPilot brings sales, stock, suppliers, expenses and insights into one fast workspace designed for busy retail counters.</p>
            <div className="mt-6 flex flex-wrap gap-2.5">
              <Link href="/register" className="rounded-xl bg-emerald-600 px-5 py-3 text-sm font-bold text-white hover:bg-emerald-700">Create your workspace</Link>
              <Link href="/dashboard" className="rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-bold hover:border-emerald-300">View live demo</Link>
            </div>
            <div className="mt-6 flex gap-6 text-sm">
              <div><div className="text-xl font-extrabold">2 min</div><div className="text-slate-500">to first sale</div></div>
              <div><div className="text-xl font-extrabold">16</div><div className="text-slate-500">workspace screens</div></div>
              <div><div className="text-xl font-extrabold">PDF + CSV</div><div className="text-slate-500">instant exports</div></div>
            </div>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_24px_60px_-24px_rgba(5,150,105,0.35)]">
            <div className="flex items-center justify-between">
              <div className="text-sm font-bold">Today&apos;s overview</div>
              <div className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-bold text-emerald-800">Live</div>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
              {[['Revenue', '৳ 24,580', '38 orders'], ['Net profit', '৳ 6,140', '+18% vs yesterday'], ['Low stock', '7 items', '3 need reorder'], ['Pending dues', '৳ 3,900', '6 customers']].map(([a, b, c]) => (
                <div key={a} className="rounded-2xl border border-slate-100 bg-slate-50 p-3.5">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{a}</div>
                  <div className="mt-1 text-lg font-extrabold">{b}</div>
                  <div className="text-xs text-slate-500">{c}</div>
                </div>
              ))}
            </div>
            <div className="mt-4 rounded-2xl bg-slate-950 p-4 text-white">
              <div className="text-xs font-semibold text-slate-300">AI suggestion</div>
              <div className="mt-1 text-sm">Rice 1kg is selling 2.4x faster this week. Reorder 40 units before Friday.</div>
            </div>
          </div>
        </div>

        <div className="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.t} className="rounded-2xl border border-slate-200 bg-white p-5">
              <div className="text-[15px] font-bold">{f.t}</div>
              <div className="mt-1 text-sm leading-relaxed text-slate-500">{f.d}</div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
