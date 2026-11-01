import { ArrowLeft, ArrowRight, Building2, CheckCircle2, FileText, ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiPost } from '../api/client';
import { useAuth } from '../auth/AuthContext';

export default function NewApplication() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [type, setType] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const institutionLinked = Boolean(user?.institution_id);
  const applicationTypeReady = type.trim().length >= 2;
  const readyChecks = Number(institutionLinked) + Number(applicationTypeReady);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const result = await apiPost<{ id: string }>('/applications', { application_type: type });
      navigate(`/applications/${result.id}`);
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not create application'); }
    finally { setBusy(false); }
  }

  return <div className="mx-auto max-w-3xl space-y-5">
    <Link to="/applications" className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-brand-blue"><ArrowLeft size={14} />Back to applications</Link>
    <header><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Application management</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">Start a new application</h1><p className="mt-1 text-sm text-slate-500">Submit an application for your registered institution.</p></header>
    <section className="enterprise-card overflow-hidden">
      <div className="border-b border-slate-100 bg-slate-50/60 px-5 py-4"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-brand-blue"><FileText size={17} /></span><div><h2 className="text-sm font-bold text-slate-800">Application details</h2><p className="text-[10px] text-slate-500">You can add supporting documents after submission.</p></div></div></div>
      <form onSubmit={submit} className="space-y-5 p-5 md:p-7">
        <div className="flex items-start gap-3 rounded-xl border border-blue-100 bg-blue-50/60 p-4"><Building2 size={17} className="mt-0.5 shrink-0 text-brand-blue" /><p className="text-xs leading-5 text-slate-600">Your institution and region are securely linked to your account and will be included automatically.</p></div>
        <label className="block text-xs font-semibold text-slate-700">Application type<input required minLength={2} maxLength={100} value={type} onChange={(event) => setType(event.target.value)} placeholder="e.g. New Institution, Renewal, Program Expansion" className="mt-2 h-11 w-full px-3.5 text-sm" /><span className="mt-1.5 block text-[10px] font-normal text-slate-400">Enter the application category as specified for your institution.</span></label>
        <section aria-label="Application readiness checklist" className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
          <div className="flex items-center justify-between gap-3"><div><h2 className="text-xs font-bold text-slate-800">Ready to submit?</h2><p className="mt-1 text-[10px] text-slate-500">A quick check before this record enters the workflow.</p></div><span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-semibold text-brand-blue">{readyChecks}/2 ready</span></div>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            <li className="flex items-center gap-2 text-[11px] text-slate-600"><CheckCircle2 size={14} className={institutionLinked ? 'text-emerald-600' : 'text-slate-300'} />Institution account {institutionLinked ? 'is linked' : 'needs to be linked'}</li>
            <li className="flex items-center gap-2 text-[11px] text-slate-600"><CheckCircle2 size={14} className={applicationTypeReady ? 'text-emerald-600' : 'text-slate-300'} />Application type {applicationTypeReady ? 'entered' : 'required'}</li>
          </ul>
          {!institutionLinked && <p role="alert" className="mt-3 text-[10px] font-medium text-rose-700">Ask a workspace administrator to link your institution before submitting.</p>}
          <p className="mt-3 border-t border-slate-200 pt-3 text-[10px] leading-5 text-slate-500"><b>Next:</b> After creation, attach relevant supporting files from Documents. The workspace tracks file review status; it does not determine official eligibility or document completeness.</p>
        </section>
        <div className="flex items-start gap-2 rounded-lg bg-slate-50 p-3 text-[10px] leading-5 text-slate-500"><ShieldCheck size={14} className="mt-0.5 shrink-0 text-emerald-600" />Submitting creates a traceable workflow record. Authorized officers will review your application through each configured stage.</div>
        {error && <p role="alert" className="rounded-lg border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
        <div className="flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-4"><Link to="/applications" className="inline-flex h-10 items-center rounded-lg border border-slate-200 px-4 text-xs font-semibold text-slate-600 hover:bg-slate-50">Cancel</Link><button disabled={busy || !institutionLinked || !applicationTypeReady} className="inline-flex h-10 items-center gap-2 rounded-lg bg-brand-blue px-4 text-xs font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50">{busy ? 'Submitting…' : 'Submit application'}{!busy && <ArrowRight size={14} />}</button></div>
      </form>
    </section>
    <div className="flex items-center gap-2 text-[10px] text-slate-400"><CheckCircle2 size={13} className="text-emerald-500" />Application activity is recorded for transparent review.</div>
  </div>;
}
