import { ArrowLeft, Building2, Landmark, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { apiGet } from '../api/client';

type Institution = { id: number; name: string; region: string };

const formControlClass = 'mt-1.5 h-10 w-full rounded-lg border border-slate-300 bg-white px-3 text-xs text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-blue-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-400';

export default function Register() {
  const { register, user } = useAuth();
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [form, setForm] = useState({ email: '', password: '', full_name: '', institution_id: 0 });
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => { apiGet<Institution[]>('/auth/institutions').then(setInstitutions).catch((err: Error) => setError(err.message)); }, []);
  if (user) return <Navigate to="/dashboard" replace />;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try { await register(form); setSubmitted(true); }
    catch (err) { setError(err instanceof Error ? err.message : 'Unable to register'); }
    finally { setBusy(false); }
  }

  return <div className="min-h-screen bg-surface lg:grid lg:grid-cols-[.8fr_1.2fr]">
    <aside className="relative hidden min-h-screen overflow-hidden bg-brand-navy p-12 text-white lg:flex lg:flex-col">
      <div className="absolute -bottom-36 -right-36 h-[470px] w-[470px] rounded-full border border-white/[.08]" />
      <div className="flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10"><Landmark size={22} /></span><span><b className="block text-sm">NEXORA AICTE</b><span className="text-[10px] text-blue-200">Approval &amp; Compliance Intelligence</span></span></div>
      <div className="relative my-auto max-w-md py-12"><span className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-400/15 text-blue-200"><Building2 size={22} /></span><h1 className="page-title mt-7 text-4xl font-bold leading-tight">A trusted workspace for institutional teams.</h1><p className="mt-4 text-sm leading-7 text-slate-300">Request access to submit applications, manage supporting documents and track compliance commitments.</p><div className="mt-8 flex items-start gap-3 rounded-xl border border-white/10 bg-white/[.06] p-4"><ShieldCheck size={18} className="mt-0.5 shrink-0 text-emerald-300" /><p className="text-xs leading-5 text-slate-300">New accounts are reviewed by an administrator before access is activated.</p></div></div>
      <p className="text-[10px] text-slate-400">Fictional approval workflow prototype · No connection to AICTE systems</p>
    </aside>
    <main className="flex min-h-screen flex-col px-5 py-7 sm:px-10 lg:px-16">
      <Link to="/login" className="inline-flex w-fit items-center gap-2 text-xs font-semibold text-slate-500 hover:text-brand-blue"><ArrowLeft size={14} />Back to sign in</Link>
      <section className="mx-auto my-auto w-full max-w-lg py-10">
        <p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Institution access</p>
        <h2 className="page-title mt-2 text-3xl font-bold text-brand-navy">{submitted ? 'Request received' : 'Request an account'}</h2>
        {submitted ? <div className="mt-6 rounded-xl border border-emerald-100 bg-white p-5 shadow-sm"><p className="text-sm leading-6 text-slate-600">Your registration is submitted. An administrator must verify and activate your institution account before you can sign in.</p><Link to="/login" className="mt-5 inline-flex h-10 items-center rounded-lg bg-brand-blue px-4 text-xs font-semibold text-white hover:bg-blue-700">Return to sign in</Link></div> :
          <>
            <p className="mt-2 text-sm text-slate-500">Share your institutional details to request access.</p>
            <form onSubmit={submit} className="mt-7 space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
              <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-200">Full name<input required minLength={2} value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} placeholder="e.g. Ananya Sharma" autoComplete="name" className={formControlClass} /></label>
              <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-200">Work email<input required type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} placeholder="name@institution.edu" autoComplete="email" className={formControlClass} /></label>
              <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-200">Password<input required minLength={8} type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} placeholder="At least 8 characters" autoComplete="new-password" className={formControlClass} /></label>
              <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-200">Institution<select required value={form.institution_id} onChange={(event) => setForm({ ...form, institution_id: Number(event.target.value) })} className={formControlClass}><option value={0} disabled>Select your institution</option>{institutions.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.region}</option>)}</select></label>
              {error && <p role="alert" className="rounded-lg border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
              <button disabled={busy} className="h-10 w-full rounded-lg bg-brand-blue text-xs font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50">{busy ? 'Submitting request…' : 'Submit access request'}</button>
              <p className="text-center text-[10px] text-slate-400">Access remains pending until administrator verification.</p>
            </form>
          </>}
      </section>
      <footer className="text-center text-[10px] text-slate-400">© {new Date().getFullYear()} NEXORA AICTE · Secure institutional access</footer>
    </main>
  </div>;
}
