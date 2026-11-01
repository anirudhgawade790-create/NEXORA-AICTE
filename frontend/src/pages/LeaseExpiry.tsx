import { AlertTriangle, CalendarClock, CheckCircle2, FileCheck2, Landmark, UploadCloud } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { useAuth } from '../auth/AuthContext';

type LeaseData = { buckets: Record<string, { id: number; category: string; expiry_date: string; status: string }[]>; counts: Record<string, number>; reminder_intervals: number[]; note: string };

function expiryTone(status: string) {
  if (status.includes('expired') || status.includes('overdue')) return 'bg-rose-50 text-rose-700';
  if (status.includes('verification')) return 'bg-blue-50 text-blue-700';
  if (status.includes('soon') || status.includes('awaited')) return 'bg-amber-50 text-amber-700';
  return 'bg-emerald-50 text-emerald-700';
}

export default function LeaseExpiry() {
  const { user } = useAuth();
  const [data, setData] = useState<LeaseData | null>(null);
  const [files, setFiles] = useState<Record<number, File>>({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState<number | null>(null);

  async function load() {
    try { setData(await apiGet<LeaseData>('/lease/dashboard')); setError(''); }
    catch (err) { setError(err instanceof Error ? err.message : 'Unable to load lease dashboard'); }
  }
  useEffect(() => { void load(); }, []);

  async function renew(id: number) {
    const file = files[id];
    if (!file) return;
    if (!['application/pdf', 'image/jpeg', 'image/png'].includes(file.type) || file.size > 10 * 1024 * 1024) { setError('Use a PDF, JPG or PNG up to 10 MB.'); return; }
    const form = new FormData();
    form.append('file', file);
    form.append('category', 'Lease Documents');
    setBusy(id);
    try { await apiPost(`/lease/${id}/renew`, form); setFiles((current) => { const next = { ...current }; delete next[id]; return next; }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Renewal failed'); }
    finally { setBusy(null); }
  }

  const total = useMemo(() => Object.values(data?.counts || {}).reduce((sum, value) => sum + value, 0), [data]);

  return <div className="space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Asset &amp; validity monitoring</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">Lease management</h1><p className="mt-1 text-sm text-slate-500">Monitor lease records, renewal status and upcoming expiries.</p></div><div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[10px] text-slate-500"><Landmark size={15} className="text-brand-blue" />{data ? `${total} records` : 'Loading records'}</div></header>
    {error && <p role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
    {!data ? <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }, (_, index) => <div key={index} className="enterprise-card h-24 animate-pulse bg-slate-50" />)}</div> : <>
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{Object.entries(data.counts).map(([name, count], index) => <article key={name} className="enterprise-card flex items-center justify-between p-4"><div><p className="text-[10px] text-slate-500">{name}</p><p className="page-title mt-2 text-2xl font-bold text-brand-navy">{count}</p></div><span className={`flex h-10 w-10 items-center justify-center rounded-xl ${index === 0 ? 'bg-rose-50 text-rose-600' : index === 1 ? 'bg-amber-50 text-amber-700' : 'bg-blue-50 text-brand-blue'}`}><CalendarClock size={18} /></span></article>)}</section>
      <div className="flex items-start gap-2 rounded-xl border border-blue-100 bg-blue-50/60 p-4 text-[10px] leading-5 text-blue-900"><AlertTriangle size={15} className="mt-0.5 shrink-0" /><span>Reminder intervals: {data.reminder_intervals.join(', ')} days. {data.note}</span></div>
      <section className="space-y-4">{Object.entries(data.buckets).map(([bucket, docs]) => <article key={bucket} className="enterprise-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-600"><FileCheck2 size={17} /></span><div><h2 className="text-xs font-bold text-slate-800">{bucket}</h2><p className="mt-0.5 text-[10px] text-slate-500">Lease validity and replacement records</p></div></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-semibold text-slate-600">{docs.length}</span></div>
        {docs.length === 0 ? <p className="p-5 text-xs text-slate-500">No records in this category.</p> : <div className="divide-y divide-slate-100">{docs.map((doc) => <div key={doc.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
          <div className="flex items-center gap-3"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-50 text-slate-500"><Landmark size={15} /></span><div><p className="text-xs font-semibold text-slate-800">{doc.category}</p><p className="mt-1 text-[10px] text-slate-500">Expires {new Date(doc.expiry_date).toLocaleDateString()}</p></div></div>
          <div className="flex flex-wrap items-center gap-2"><span className={`rounded-full px-2.5 py-1 text-[9px] font-semibold ${expiryTone(doc.status)}`}>{doc.status.replace(/_/g, ' ')}</span>
            {bucket === 'Renewal Awaited' && user?.role === 'institution' && <><label className="flex h-8 cursor-pointer items-center gap-2 rounded-lg border border-slate-200 px-2.5 text-[10px] text-slate-600"><UploadCloud size={13} />{files[doc.id]?.name || 'Choose renewal'}<input type="file" accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png" onChange={(event) => { const selected = event.target.files?.[0]; if (selected) setFiles({ ...files, [doc.id]: selected }); }} className="sr-only" /></label><button disabled={!files[doc.id] || busy === doc.id} onClick={() => void renew(doc.id)} className="h-8 rounded-lg bg-brand-blue px-3 text-[10px] font-semibold text-white hover:bg-blue-700 disabled:opacity-40">{busy === doc.id ? 'Uploading…' : 'Upload renewal'}</button></>}
          </div>
        </div>)}</div>}
      </article>)}</section>
      {!Object.keys(data.buckets).length && <div className="enterprise-card p-10 text-center"><CheckCircle2 size={25} className="mx-auto text-emerald-500" /><p className="mt-3 text-sm font-semibold text-slate-700">No lease records available</p><p className="mt-1 text-xs text-slate-500">Lease data for your portfolio will appear here.</p></div>}
    </>}
  </div>;
}
