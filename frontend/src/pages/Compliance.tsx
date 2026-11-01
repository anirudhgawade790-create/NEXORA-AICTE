import { AlertCircle, CalendarClock, CheckCircle2, ClipboardCheck, FileCheck2, Plus, ShieldCheck } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { useAuth } from '../auth/AuthContext';

type ComplianceItem = { id: number; description: string; due_date: string; status: string; days_remaining: number; institution_id: number; evidence_document_id?: number };

function stateStyle(days: number, status: string) {
  if (status === 'verified') return 'bg-emerald-50 text-emerald-700';
  if (days < 0) return 'bg-rose-50 text-rose-700';
  if (days <= 30) return 'bg-amber-50 text-amber-700';
  return 'bg-blue-50 text-blue-700';
}

export default function Compliance() {
  const { user } = useAuth();
  const [items, setItems] = useState<ComplianceItem[]>([]);
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [evidence, setEvidence] = useState<Record<number, string>>({});
  const [remarks, setRemarks] = useState<Record<number, string>>({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    try { setItems(await apiGet<ComplianceItem[]>('/compliance')); setError(''); }
    catch (err) { setError(err instanceof Error ? err.message : 'Unable to load compliance'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);

  async function create(event: React.FormEvent) {
    event.preventDefault();
    try { await apiPost('/compliance', { description, due_date: new Date(dueDate).toISOString() }); setDescription(''); setDueDate(''); setSuccess('Undertaking created.'); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Create failed'); }
  }
  async function submitEvidence(id: number) {
    try { await apiPost(`/compliance/${id}/evidence?evidence_document_id=${encodeURIComponent(evidence[id] || '')}`); setSuccess('Evidence submitted for review.'); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Evidence submission failed'); }
  }
  async function verify(id: number, status: string) {
    if (!remarks[id]?.trim()) { setError('Please add verification remarks before submitting.'); return; }
    try { await apiPost(`/compliance/${id}/verify`, { status, remarks: remarks[id].trim() }); setSuccess(status === 'verified' ? 'Compliance item verified.' : 'Deficiency request recorded.'); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Verification failed'); }
  }

  const counts = useMemo(() => ({
    verified: items.filter((item) => item.status === 'verified').length,
    overdue: items.filter((item) => item.days_remaining < 0 && item.status !== 'verified').length,
    dueSoon: items.filter((item) => item.days_remaining >= 0 && item.days_remaining <= 30 && item.status !== 'verified').length,
  }), [items]);
  const completion = items.length ? Math.round((counts.verified / items.length) * 100) : 0;
  const canVerify = ['admin', 'regional_officer', 'bureau_officer'].includes(user?.role || '');

  return <div className="space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Compliance &amp; governance</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">Compliance monitoring</h1><p className="mt-1 text-sm text-slate-500">Track evidence, deadlines and institutional obligations.</p></div><div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[10px] text-slate-500"><ShieldCheck size={15} className="text-emerald-600" />Role-scoped records</div></header>

    {error && <p role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
    {success && <p role="status" className="rounded-xl border border-emerald-100 bg-emerald-50 p-3 text-xs text-emerald-700">{success}</p>}

    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <article className="enterprise-card p-4"><div className="flex items-center justify-between"><span className="text-[11px] text-slate-500">Total obligations</span><ClipboardCheck size={17} className="text-blue-600" /></div><p className="page-title mt-3 text-2xl font-bold text-brand-navy">{loading ? '—' : items.length}</p><p className="mt-1 text-[10px] text-slate-400">Visible in your portfolio</p></article>
      <article className="enterprise-card p-4"><div className="flex items-center justify-between"><span className="text-[11px] text-slate-500">Verified</span><CheckCircle2 size={17} className="text-emerald-600" /></div><p className="page-title mt-3 text-2xl font-bold text-brand-navy">{loading ? '—' : counts.verified}</p><p className="mt-1 text-[10px] text-slate-400">Evidence accepted</p></article>
      <article className="enterprise-card p-4"><div className="flex items-center justify-between"><span className="text-[11px] text-slate-500">Due in 30 days</span><CalendarClock size={17} className="text-amber-600" /></div><p className="page-title mt-3 text-2xl font-bold text-brand-navy">{loading ? '—' : counts.dueSoon}</p><p className="mt-1 text-[10px] text-slate-400">Approaching deadline</p></article>
      <article className="enterprise-card p-4"><div className="flex items-center justify-between"><span className="text-[11px] text-slate-500">Overdue</span><AlertCircle size={17} className="text-rose-600" /></div><p className="page-title mt-3 text-2xl font-bold text-brand-navy">{loading ? '—' : counts.overdue}</p><p className="mt-1 text-[10px] text-slate-400">Needs attention</p></article>
    </section>

    <section className="enterprise-card flex flex-wrap items-center gap-5 p-5">
      <div className="flex h-[92px] w-[92px] shrink-0 items-center justify-center rounded-full" style={{ background: `conic-gradient(#10b981 ${completion}%, #e8edf3 ${completion}% 100%)` }}><div className="flex h-[72px] w-[72px] flex-col items-center justify-center rounded-full bg-white"><b className="text-lg text-brand-navy">{loading ? '—' : `${completion}%`}</b><span className="text-[8px] uppercase tracking-wide text-slate-400">Verified</span></div></div>
      <div className="min-w-0 flex-1"><h2 className="text-sm font-bold text-slate-800">Compliance completion</h2><p className="mt-1 max-w-xl text-xs leading-5 text-slate-500">Completion is calculated from verified obligations in the records available to your account.</p><div className="mt-3 h-2 max-w-lg overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${completion}%` }} /></div></div>
      <span className="rounded-lg bg-slate-50 px-3 py-2 text-[10px] text-slate-500">{counts.verified} of {items.length} verified</span>
    </section>

    {user?.role === 'institution' && <form onSubmit={create} className="enterprise-card grid gap-3 p-5 md:grid-cols-[1fr_auto_auto] md:items-end">
      <div><p className="text-[11px] font-bold text-slate-800">Create an undertaking</p><label className="mt-3 block text-[10px] font-medium text-slate-600">Description<input required value={description} onChange={(event) => setDescription(event.target.value)} className="mt-1.5 h-10 w-full px-3 text-xs" placeholder="Describe the compliance requirement" /></label></div>
      <label className="block text-[10px] font-medium text-slate-600">Due date<input required type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} className="mt-1.5 h-10 w-full px-3 text-xs" /></label>
      <button className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-brand-blue px-4 text-xs font-semibold text-white transition hover:bg-blue-700"><Plus size={15} />Add obligation</button>
    </form>}

    <section className="enterprise-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="text-sm font-bold text-slate-800">Obligations &amp; evidence</h2><p className="mt-1 text-[10px] text-slate-500">Review status and take action on each record.</p></div><FileCheck2 size={17} className="text-slate-400" /></div>
      {loading ? <div className="space-y-3 p-5">{Array.from({ length: 3 }, (_, index) => <div key={index} className="h-28 animate-pulse rounded-xl bg-slate-100" />)}</div> : items.length === 0 ? <div className="p-12 text-center"><CheckCircle2 size={26} className="mx-auto text-emerald-500" /><p className="mt-3 text-sm font-semibold text-slate-700">No compliance records found</p><p className="mt-1 text-xs text-slate-500">New obligations will appear here when available.</p></div> : <div className="divide-y divide-slate-100">{items.map((item) => <article key={item.id} className="p-5 transition hover:bg-slate-50/50">
        <div className="flex flex-wrap items-start justify-between gap-3"><div className="min-w-0"><h3 className="text-xs font-semibold text-slate-800">{item.description}</h3><div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] text-slate-500"><span>Due {new Date(item.due_date).toLocaleDateString()}</span><span>{item.days_remaining < 0 ? `${Math.abs(item.days_remaining)} days overdue` : `${item.days_remaining} days remaining`}</span><span>Institution #{item.institution_id}</span></div></div><span className={`rounded-full px-2.5 py-1 text-[9px] font-semibold ${stateStyle(item.days_remaining, item.status)}`}>{item.status === 'verified' ? 'Verified' : item.days_remaining < 0 ? 'Overdue' : item.days_remaining <= 30 ? 'Due soon' : 'On track'}</span></div>
        {user?.role === 'institution' && item.status !== 'verified' && <div className="mt-4 flex flex-wrap gap-2"><input type="number" aria-label="Evidence document ID" placeholder="Evidence document ID" value={evidence[item.id] || ''} onChange={(event) => setEvidence({ ...evidence, [item.id]: event.target.value })} className="h-9 w-48 px-3 text-[10px]" /><button onClick={() => void submitEvidence(item.id)} disabled={!evidence[item.id]} className="rounded-lg bg-brand-blue px-3 text-[10px] font-semibold text-white transition hover:bg-blue-700 disabled:opacity-40">Submit evidence</button></div>}
        {canVerify && item.status !== 'verified' && <div className="mt-4 grid gap-2 sm:grid-cols-[1fr_auto_auto]"><input aria-label="Verification remarks" placeholder="Verification remarks (required)" value={remarks[item.id] || ''} onChange={(event) => setRemarks({ ...remarks, [item.id]: event.target.value })} className="h-9 px-3 text-[10px]" /><button onClick={() => void verify(item.id, 'verified')} disabled={!remarks[item.id]?.trim()} className="rounded-lg bg-emerald-600 px-3 py-2 text-[10px] font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-40">Verify evidence</button><button onClick={() => void verify(item.id, 'deficient')} disabled={!remarks[item.id]?.trim()} className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[10px] font-semibold text-amber-800 transition hover:bg-amber-100 disabled:opacity-40">Request deficiency</button></div>}
      </article>)}</div>}
    </section>
  </div>;
}
