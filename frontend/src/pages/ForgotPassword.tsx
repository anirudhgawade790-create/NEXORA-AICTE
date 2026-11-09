import { ArrowLeft, KeyRound, Landmark, MailCheck } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { apiPost } from '../api/client';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const result = await apiPost<{ message: string }>('/auth/forgot-password', { email });
      setMessage(result.message);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to request a password reset');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface px-5 py-10">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900 sm:p-8">
        <Link to="/login" className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-brand-blue">
          <ArrowLeft size={14} /> Back to sign in
        </Link>
        <span className="mt-8 flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-brand-blue dark:bg-blue-950/60 dark:text-blue-300"><KeyRound size={20} /></span>
        <p className="mt-6 text-[11px] font-bold uppercase tracking-[.14em] text-brand-blue">Account recovery</p>
        <h1 className="page-title mt-2 text-3xl font-bold text-brand-navy dark:text-white">Forgot password?</h1>
        <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">Enter your account email and we’ll send a reset link if it matches an active account.</p>

        {message ? (
          <div role="status" className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
            <MailCheck size={18} className="mb-2" />
            {message}
            <p className="mt-2 text-xs">Check your inbox and spam folder. The link expires after 30 minutes.</p>
          </div>
        ) : (
          <form onSubmit={submit} className="mt-7 space-y-4">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-200">
              Work email
              <input
                required
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="name@institution.edu"
                className="mt-2 h-11 w-full px-3.5 text-sm"
              />
            </label>
            {error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
            <button disabled={busy} className="h-11 w-full rounded-lg bg-brand-blue px-4 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60">
              {busy ? 'Sending reset link…' : 'Send reset link'}
            </button>
          </form>
        )}

        <div className="mt-7 flex items-center justify-center gap-2 text-[10px] text-slate-400">
          <Landmark size={12} /> NEXORA AICTE · Secure account recovery
        </div>
      </section>
    </main>
  );
}
