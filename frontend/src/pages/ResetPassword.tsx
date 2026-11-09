import { ArrowLeft, CheckCircle2, Landmark, LockKeyhole } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { apiPost } from '../api/client';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setBusy(true);
    try {
      const result = await apiPost<{ message: string }>('/auth/reset-password', {
        token,
        new_password: password,
      });
      setSuccess(result.message);
      window.setTimeout(() => navigate('/login', { replace: true }), 1800);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to reset password');
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
        <span className="mt-8 flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-brand-blue dark:bg-blue-950/60 dark:text-blue-300"><LockKeyhole size={20} /></span>
        <p className="mt-6 text-[11px] font-bold uppercase tracking-[.14em] text-brand-blue">Account recovery</p>
        <h1 className="page-title mt-2 text-3xl font-bold text-brand-navy dark:text-white">Choose a new password</h1>
        <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">Use at least 8 characters. Your reset link can only be used once.</p>

        {success ? (
          <div role="status" className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200">
            <CheckCircle2 size={18} className="mb-2" />{success}
            <p className="mt-2 text-xs">Taking you to sign in…</p>
          </div>
        ) : !token ? (
          <div role="alert" className="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            This reset link is missing its token. Request a new one to continue.
            <Link to="/forgot-password" className="mt-3 block font-semibold underline">Request a reset link</Link>
          </div>
        ) : (
          <form onSubmit={submit} className="mt-7 space-y-4">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-200">
              New password
              <input
                required
                minLength={8}
                maxLength={72}
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="At least 8 characters"
                className="mt-2 h-11 w-full px-3.5 text-sm"
              />
            </label>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-200">
              Confirm new password
              <input
                required
                minLength={8}
                maxLength={72}
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                placeholder="Enter the password again"
                className="mt-2 h-11 w-full px-3.5 text-sm"
              />
            </label>
            {error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
            <button disabled={busy} className="h-11 w-full rounded-lg bg-brand-blue px-4 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60">
              {busy ? 'Updating password…' : 'Reset password'}
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
