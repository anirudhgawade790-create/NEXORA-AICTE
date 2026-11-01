import { ArrowRight, BadgeCheck, Building2, CheckCircle2, FileCheck2, Landmark, LockKeyhole, ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

const demoAccounts = [
  ['Administrator', 'admin@nexora-demo.in', 'AD'],
  ['Regional Officer', 'regional@nexora-demo.in', 'RO'],
  ['Bureau Officer', 'bureau@nexora-demo.in', 'BO'],
  ['EVC / Committee', 'evc@nexora-demo.in', 'EC'],
  ['Institution', 'institution@nexora-demo.in', 'IN'],
];

export default function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState(() => localStorage.getItem('nexora_remembered_email') || '');
  const [password, setPassword] = useState('demo1234');
  const [rememberEmail, setRememberEmail] = useState(Boolean(localStorage.getItem('nexora_remembered_email')));
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  if (user) return <Navigate to="/dashboard" replace />;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    setBusy(true);
    if (rememberEmail) localStorage.setItem('nexora_remembered_email', email);
    else localStorage.removeItem('nexora_remembered_email');
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-white lg:grid lg:grid-cols-[1.05fr_.95fr]">
      <section className="relative hidden min-h-screen overflow-hidden bg-brand-navy px-10 py-9 text-white lg:flex lg:flex-col xl:px-16">
        <div className="absolute -right-36 -top-32 h-[500px] w-[500px] rounded-full border border-white/[.07]" />
        <div className="absolute -right-20 -top-16 h-[360px] w-[360px] rounded-full border border-white/[.08]" />
        <div className="absolute -bottom-48 -left-28 h-[500px] w-[500px] rounded-full bg-blue-500/10 blur-3xl" />

        <Link to="/login" className="relative z-10 inline-flex w-fit items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-white/15 bg-white/10"><Landmark size={23} /></span>
          <span><b className="block text-sm tracking-wide">NEXORA AICTE</b><span className="text-[10px] text-blue-200">Approval &amp; Compliance Intelligence</span></span>
        </Link>

        <div className="relative z-10 my-auto max-w-xl py-12">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-blue-200/20 bg-blue-300/10 px-3 py-1.5 text-[11px] font-medium text-blue-100"><BadgeCheck size={14} /> A unified approval workspace</div>
          <h1 className="page-title max-w-lg text-4xl font-bold leading-[1.13] tracking-tight xl:text-[48px]">Simplifying Approvals.<br /><span className="text-blue-300">Strengthening Compliance.</span></h1>
          <p className="mt-5 max-w-lg text-sm leading-7 text-slate-300">A secure, transparent workspace for managing institutional applications, review workflows and compliance obligations.</p>

          <div className="relative mt-11 max-w-lg rounded-2xl border border-white/10 bg-white/[.06] p-5 shadow-2xl backdrop-blur-sm">
            <div className="flex items-center justify-between"><div className="flex items-center gap-2"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-400/15 text-blue-200"><FileCheck2 size={18} /></span><span><b className="block text-xs">Approval workflow</b><span className="text-[10px] text-slate-400">Clear stages. Accountable decisions.</span></span></div><span className="rounded-full bg-emerald-400/10 px-2.5 py-1 text-[9px] font-semibold text-emerald-300">LIVE STATUS</span></div>
            <div className="mt-6 grid grid-cols-4 gap-2">
              {['Submitted', 'Scrutiny', 'EVC review', 'Decision'].map((step, index) => <div key={step} className="relative">
                {index < 3 && <span className="absolute left-[58%] top-[13px] h-px w-full bg-white/15" />}
                <span className={`relative z-10 flex h-7 w-7 items-center justify-center rounded-full border ${index < 2 ? 'border-blue-300 bg-blue-400 text-white' : 'border-white/20 bg-slate-800 text-slate-400'}`}>{index < 2 ? <CheckCircle2 size={14} /> : <span className="text-[10px]">{index + 1}</span>}</span>
                <span className="mt-2 block text-[9px] text-slate-400">{step}</span>
              </div>)}
            </div>
            <div className="mt-5 flex items-center justify-between rounded-xl border border-white/[.07] bg-slate-950/25 px-3 py-2.5 text-[10px]"><span className="flex items-center gap-2 text-slate-300"><Building2 size={13} /> Institution application</span><span className="text-blue-200">Under review</span></div>
          </div>
          <div className="mt-6 flex items-center gap-2 text-[10px] text-slate-400"><ShieldCheck size={14} className="text-emerald-300" /> Role-based access · Auditable workflow · Secure document handling</div>
        </div>
        <footer className="relative z-10 flex items-center justify-between text-[10px] text-slate-400"><span>© {new Date().getFullYear()} NEXORA AICTE Prototype</span><Link to="/help" className="hover:text-white">Support &amp; guidance</Link></footer>
      </section>

      <section className="flex min-h-screen flex-col px-5 py-7 sm:px-10 lg:px-12 xl:px-20">
        <div className="mb-8 flex items-center gap-3 lg:hidden">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-navy text-white"><Landmark size={21} /></span>
          <span><b className="block text-sm text-brand-navy">NEXORA AICTE</b><span className="text-[10px] text-slate-500">Approval &amp; Compliance Intelligence</span></span>
        </div>
        <div className="mx-auto my-auto w-full max-w-[410px] py-8">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-brand-blue"><LockKeyhole size={21} /></span>
          <p className="mt-7 text-[11px] font-bold uppercase tracking-[.15em] text-brand-blue">Secure workspace access</p>
          <h2 className="page-title mt-2 text-3xl font-bold tracking-tight text-brand-navy">Welcome back</h2>
          <p className="mt-2 text-sm text-slate-500">Sign in to continue to your approval workspace.</p>

          <form onSubmit={submit} className="mt-8 space-y-5">
            <label className="block text-xs font-semibold text-slate-700">Work email
              <input required type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="name@institution.edu" className="mt-2 h-11 w-full px-3.5 text-sm" />
            </label>
            <label className="block text-xs font-semibold text-slate-700">Password
              <input required type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" className="mt-2 h-11 w-full px-3.5 text-sm" />
            </label>
            <div className="flex items-center justify-between">
              <label className="flex cursor-pointer items-center gap-2 text-xs text-slate-600"><input type="checkbox" checked={rememberEmail} onChange={(event) => setRememberEmail(event.target.checked)} className="h-4 w-4 rounded border-slate-300 accent-blue-600" />Remember email</label>
              <Link to="/help" className="text-xs font-semibold text-brand-blue hover:underline">Need help signing in?</Link>
            </div>
            {error && <p role="alert" className="rounded-lg border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
            <button disabled={busy} className="flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-brand-blue px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60">{busy ? 'Signing in…' : 'Sign in securely'}{!busy && <ArrowRight size={16} />}</button>
          </form>

          <div className="my-7 flex items-center gap-3"><span className="h-px flex-1 bg-slate-200" /><span className="text-[10px] font-medium uppercase tracking-wide text-slate-400">Demo access</span><span className="h-px flex-1 bg-slate-200" /></div>
          <p className="mb-3 text-[11px] text-slate-500">Select a role to prefill a fictional demo account.</p>
          <div className="grid grid-cols-2 gap-2">
            {demoAccounts.map(([role, account, initials]) => <button key={account} type="button" onClick={() => { setEmail(account); setPassword('demo1234'); }} className="flex items-center gap-2.5 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-left transition hover:border-blue-200 hover:bg-blue-50/50">
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-100 text-[9px] font-bold text-slate-600">{initials}</span><span className="min-w-0"><span className="block truncate text-[10px] font-semibold text-slate-700">{role}</span><span className="block text-[9px] text-slate-400">Demo account</span></span>
            </button>)}
          </div>
          <p className="mt-3 text-center text-[10px] text-slate-400">Demo password: <code className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-600">demo1234</code></p>
          <p className="mt-7 text-center text-xs text-slate-500">New institution user? <Link to="/register" className="font-semibold text-brand-blue hover:underline">Request account access</Link></p>
        </div>
        <footer className="flex flex-wrap justify-center gap-x-5 gap-y-2 py-3 text-[10px] text-slate-400"><span className="flex items-center gap-1"><ShieldCheck size={12} />Secure sign-in</span><span>Fictional workflow prototype</span><Link to="/help" className="hover:text-slate-600">Contact support</Link></footer>
      </section>
    </div>
  );
}
