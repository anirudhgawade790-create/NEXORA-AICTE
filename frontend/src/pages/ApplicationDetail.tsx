import { Activity, AlertCircle, ArrowLeft, ArrowRight, CalendarClock, CheckCircle2, Clock3, FileCheck2, Landmark, MessageSquareText, ShieldCheck, UserRound } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { apiGet, apiPost } from '../api/client';
import { useAuth } from '../auth/AuthContext';

type Detail = {
  id: string; institution: string; region: string; type: string; workflow_path_label: string;
  workflow_stages: string[]; current_stage: string; status: string;
  officer: string; daysPending: number; deadline: string | null;
  timeline: { id: number; stage: string; entered_at: string; exited_at: string | null; status: string; reason: string | null; actor_user_id: number }[];
  observations: { id: number; observation_text: string; is_deficiency: boolean; created_at: string }[];
  documents: { id: number; category: string; file_name: string; status: string }[];
};

function formatLabel(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function ApplicationDetail() {
  const { id = '' } = useParams();
  const { user } = useAuth();
  const [item, setItem] = useState<Detail | null>(null);
  const [reason, setReason] = useState('');
  const [observation, setObservation] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function load() {
    try { setItem(await apiGet<Detail>(`/applications/${encodeURIComponent(id)}`)); setError(''); }
    catch (err) { setError(err instanceof Error ? err.message : 'Unable to load application'); }
  }
  useEffect(() => { void load(); }, [id]);

  async function transition(action: string) {
    if ((action === 'return' || action === 'reject') && !reason.trim()) return;
    if (!window.confirm(`Proceed with "${action}" for ${id}?`)) return;
    setBusy(true);
    try {
      await apiPost(`/applications/${encodeURIComponent(id)}/transition`, { action, reason: reason.trim() || undefined });
      setReason('');
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Workflow update failed'); }
    finally { setBusy(false); }
  }

  async function addObservation() {
    try {
      await apiPost(`/applications/${encodeURIComponent(id)}/observations`, { observation_text: observation, is_deficiency: true, severity: 'medium' });
      setObservation('');
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to save observation'); }
  }

  if (error && !item) return <div role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-5 text-sm text-rose-700">{error}</div>;
  if (!item) return <div className="enterprise-card h-48 animate-pulse bg-slate-50" />;
  const officer = ['admin', 'regional_officer', 'bureau_officer'].includes(user?.role || '');
  const currentIndex = item.workflow_stages.indexOf(item.current_stage);
  const terminal = ['approved', 'rejected'].includes(item.status);
  const verifiedDocuments = item.documents.filter((document) => document.status === 'verified').length;
  const documentsNeedingAttention = item.documents.filter(
    (document) => ['deficient', 'rejected', 'expired', 'expiring_soon'].includes(document.status),
  ).length;
  const evidenceProgress = item.documents.length
    ? Math.round((verifiedDocuments / item.documents.length) * 100)
    : 0;

  return <div className="space-y-5">
    <Link to="/applications" className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 transition hover:text-brand-blue"><ArrowLeft size={14} />Back to applications</Link>
    <section className="enterprise-card overflow-hidden">
      <div className="flex flex-wrap items-start justify-between gap-5 p-5 md:p-7">
        <div><p className="text-[10px] font-bold uppercase tracking-[.13em] text-brand-blue">Application record</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">{item.id}</h1><p className="mt-2 flex items-center gap-2 text-sm text-slate-600"><Landmark size={15} className="text-slate-400" />{item.institution}<span className="text-slate-300">·</span>{item.region}</p></div>
        <span className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize ${item.status === 'approved' ? 'bg-emerald-50 text-emerald-700' : item.status === 'rejected' ? 'bg-rose-50 text-rose-700' : item.status === 'returned' ? 'bg-amber-50 text-amber-700' : 'bg-blue-50 text-blue-700'}`}>{formatLabel(item.status)}</span>
      </div>
      <div className="grid gap-4 border-t border-slate-100 bg-slate-50/60 px-5 py-4 sm:grid-cols-2 lg:grid-cols-5 md:px-7">
        <div><p className="text-[10px] text-slate-400">Application type</p><p className="mt-1 text-xs font-semibold text-slate-700">{item.type}</p></div>
        <div><p className="text-[10px] text-slate-400">Selected example route</p><p className="mt-1 text-xs font-semibold text-slate-700">{item.workflow_path_label}</p></div>
        <div><p className="text-[10px] text-slate-400">Assigned officer</p><p className="mt-1 flex items-center gap-1.5 text-xs font-semibold text-slate-700"><UserRound size={13} className="text-slate-400" />{item.officer}</p></div>
        <div><p className="text-[10px] text-slate-400">Days in process</p><p className="mt-1 flex items-center gap-1.5 text-xs font-semibold text-slate-700"><Clock3 size={13} className="text-slate-400" />{item.daysPending} days</p></div>
        <div><p className="text-[10px] text-slate-400">Current deadline</p><p className="mt-1 flex items-center gap-1.5 text-xs font-semibold text-slate-700"><CalendarClock size={13} className="text-slate-400" />{item.deadline ? new Date(item.deadline).toLocaleDateString() : 'Not set'}</p></div>
      </div>
      <div className="overflow-x-auto border-t border-slate-100 px-5 py-6 md:px-7">
        <div className="flex min-w-[690px] items-start">
          {item.workflow_stages.map((stage, index) => {
            const complete = terminal || (currentIndex >= 0 && index < currentIndex);
            const active = !terminal && index === currentIndex;
            return <div key={stage} className="relative flex flex-1 flex-col items-center text-center">
              {index > 0 && <span className={`absolute right-1/2 top-[13px] h-px w-full ${complete || active ? 'bg-blue-500' : 'bg-slate-200'}`} />}
              <span className={`relative z-10 flex h-7 w-7 items-center justify-center rounded-full border ${complete ? 'border-blue-600 bg-blue-600 text-white' : active ? 'border-blue-600 bg-white text-blue-700 ring-4 ring-blue-50' : 'border-slate-200 bg-white text-slate-400'}`}>{complete ? <CheckCircle2 size={15} /> : <span className="text-[10px]">{index + 1}</span>}</span>
              <span className={`mt-2 max-w-24 text-[9px] ${active ? 'font-bold text-brand-blue' : complete ? 'font-medium text-slate-700' : 'text-slate-400'}`}>{formatLabel(stage)}</span>
            </div>;
          })}
        </div>
      </div>
    </section>

    {error && <p role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}

    {officer && !terminal && <section className="enterprise-card p-5">
      <div className="mb-4 flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-brand-blue"><ShieldCheck size={18} /></span><div><h2 className="text-sm font-bold text-slate-800">Workflow action</h2><p className="text-[11px] text-slate-500">Move the application forward or record a decision.</p></div></div>
      <label className="block text-[11px] font-semibold text-slate-600">Reason <span className="font-normal text-slate-400">(required for return or rejection)</span><textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={2} className="mt-2 w-full p-3 text-xs" /></label>
      <div className="mt-3 flex flex-wrap gap-2"><button disabled={busy} onClick={() => transition('forward')} className="inline-flex items-center gap-2 rounded-lg bg-brand-blue px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50">Advance application <ArrowRight size={14} /></button><button disabled={busy || !reason.trim()} onClick={() => transition('return')} className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-xs font-semibold text-amber-800 transition hover:bg-amber-100 disabled:opacity-50">Return for deficiency</button><button disabled={busy || !reason.trim()} onClick={() => transition('reject')} className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-100 disabled:opacity-50">Reject</button></div>
    </section>}
    {user?.role === 'institution' && item.status === 'returned' && <button onClick={() => transition('resubmit')} className="rounded-lg bg-emerald-600 px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-emerald-700">Resubmit application</button>}

    <div className="grid gap-5 xl:grid-cols-[1.05fr_.95fr]">
      <section className="enterprise-card p-5">
        <div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-brand-blue"><Activity size={16} /></span><div><h2 className="text-sm font-bold text-slate-800">Activity timeline</h2><p className="text-[10px] text-slate-500">Recorded workflow and review history</p></div></div>
        {item.timeline.length ? <ol className="mt-6 space-y-0">{item.timeline.map((stage, index) => <li key={stage.id} className="relative flex gap-3 pb-6 last:pb-0">
          {index < item.timeline.length - 1 && <span className="absolute left-[13px] top-7 h-full w-px bg-slate-200" />}
          <span className={`relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${stage.status === 'returned' ? 'bg-amber-50 text-amber-600' : stage.status === 'completed' ? 'bg-emerald-50 text-emerald-600' : 'bg-blue-50 text-blue-600'}`}>{stage.status === 'returned' ? <AlertCircle size={14} /> : stage.status === 'completed' ? <CheckCircle2 size={14} /> : <Clock3 size={14} />}</span>
          <div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-xs font-semibold text-slate-800">{formatLabel(stage.stage)}</p><span className="text-[9px] capitalize text-slate-400">{stage.status}</span></div><p className="mt-1 text-[10px] text-slate-500">{new Date(stage.entered_at).toLocaleString()} · User #{stage.actor_user_id}</p>{stage.reason && <p className="mt-2 rounded-lg bg-slate-50 p-2.5 text-[11px] leading-5 text-slate-600">{stage.reason}</p>}</div>
        </li>)}</ol> : <p className="mt-5 text-xs text-slate-500">No timeline entries.</p>}
      </section>

      <div className="space-y-5">
        <section className="enterprise-card p-5"><div className="flex items-center justify-between gap-3"><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-50 text-cyan-700"><FileCheck2 size={16} /></span><div><h2 className="text-sm font-bold text-slate-800">Supporting documents</h2><p className="text-[10px] text-slate-500">Evidence review progress · {verifiedDocuments}/{item.documents.length} verified</p></div></div>{user?.role === 'institution' && <Link to={`/documents?application_id=${encodeURIComponent(item.id)}`} className="shrink-0 rounded-lg bg-brand-blue px-3 py-2 text-[10px] font-semibold text-white transition hover:bg-blue-700">Add evidence</Link>}</div>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${evidenceProgress}%` }} /></div>
          <p className="mt-2 text-[9px] text-slate-400">Tracks review status of linked files only; this is not an official completeness or eligibility check.</p>
          {documentsNeedingAttention > 0 && <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-[10px] font-medium text-amber-800">{documentsNeedingAttention} linked {documentsNeedingAttention === 1 ? 'file needs' : 'files need'} attention.</p>}
          {item.documents.length ? <div className="mt-4 divide-y divide-slate-100">{item.documents.map((doc) => <div key={doc.id} className="flex items-center justify-between gap-3 py-3"><div className="flex min-w-0 items-center gap-2"><FileCheck2 size={15} className="shrink-0 text-slate-400" /><span className="min-w-0"><span className="block truncate text-xs font-semibold text-slate-700">{doc.file_name}</span><span className="text-[10px] text-slate-500">{doc.category}</span></span></div><span className="shrink-0 rounded-full bg-slate-100 px-2 py-1 text-[9px] capitalize text-slate-600">{doc.status}</span></div>)}</div> : <p className="mt-4 text-xs text-slate-500">No linked documents.</p>}
        </section>

        <section className="enterprise-card p-5"><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-700"><MessageSquareText size={16} /></span><div><h2 className="text-sm font-bold text-slate-800">Scrutiny observations</h2><p className="text-[10px] text-slate-500">Review notes and deficiencies</p></div></div>
          {item.observations.length ? <div className="mt-4 space-y-2">{item.observations.map((entry) => <div key={entry.id} className="rounded-lg border border-slate-100 p-3"><div className="flex items-center justify-between gap-2"><span className={`rounded-full px-2 py-1 text-[9px] font-semibold ${entry.is_deficiency ? 'bg-amber-50 text-amber-700' : 'bg-blue-50 text-blue-700'}`}>{entry.is_deficiency ? 'Deficiency' : 'Observation'}</span><time className="text-[9px] text-slate-400">{new Date(entry.created_at).toLocaleDateString()}</time></div><p className="mt-2 text-xs leading-5 text-slate-700">{entry.observation_text}</p></div>)}</div> : <p className="mt-4 text-xs text-slate-500">No scrutiny observations.</p>}
          {officer && <div className="mt-4 border-t border-slate-100 pt-4"><label className="block text-[10px] font-semibold text-slate-600">Add a scrutiny note<textarea aria-label="Add scrutiny observation" value={observation} onChange={(event) => setObservation(event.target.value)} placeholder="Record an observation for this application" rows={2} className="mt-2 w-full p-3 text-xs" /></label><button disabled={!observation.trim()} onClick={addObservation} className="mt-2 rounded-lg border border-slate-200 px-3 py-2 text-[10px] font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40">Add observation</button></div>}
        </section>
      </div>
    </div>
  </div>;
}
