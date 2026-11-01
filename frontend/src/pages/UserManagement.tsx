import { Activity, Building2, ShieldCheck, UserPlus, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { apiGet, apiPost, apiPut } from '../api/client';

type UserRow = { id: number; email: string; full_name: string; role: string; region: string | null; institution_id: number | null; is_active: boolean };
export default function UserManagement() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [regions, setRegions] = useState<Record<number, string>>({});
  const [form, setForm] = useState({ email: '', full_name: '', password: '', role: 'institution', region: '', institution_id: '' });
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  async function load() { try { setUsers(await apiGet<UserRow[]>('/users')); } catch (err) { setError(err instanceof Error ? err.message : 'Unable to load users'); } }
  useEffect(() => { void load(); }, []);
  async function create(event: React.FormEvent) {
    event.preventDefault();
    try { await apiPost('/users', { ...form, institution_id: form.institution_id ? Number(form.institution_id) : null, region: form.region || null }); setForm({ email: '', full_name: '', password: '', role: 'institution', region: '', institution_id: '' }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not create user'); }
  }
  async function update(user: UserRow, is_active: boolean) {
    try { await apiPut(`/users/${user.id}`, { is_active }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Update failed'); }
  }
  async function updateRegion(userId: number) {
    try { await apiPut(`/users/${userId}`, { region: regions[userId] || null }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Region update failed'); }
  }
  async function reset() {
    if (!window.confirm('Reset all database records to fictional demo seed data?')) return;
    try { await apiPost('/admin/reset-demo-data'); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Reset failed'); }
  }
  async function runMonitor() {
    try { const result = await apiPost<{ overdue_applications: number; new_escalations: number }>('/admin/run-monitor'); setNotice(`Monitor complete: ${result.overdue_applications} overdue cases, ${result.new_escalations} new escalation(s).`); }
    catch (err) { setError(err instanceof Error ? err.message : 'Monitor failed'); }
  }
  return <div className="space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Administration · Access control</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">User &amp; role management</h1><p className="mt-1 text-sm text-slate-500">Manage workspace accounts, roles and regional assignments.</p></div>
      <div className="flex flex-wrap gap-2"><button onClick={runMonitor} className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-[10px] font-semibold text-slate-700 transition hover:bg-slate-50"><Activity size={14} className="text-brand-blue" />Run deadline monitor</button><button onClick={reset} className="h-9 rounded-lg border border-rose-200 bg-white px-3 text-[10px] font-semibold text-rose-700 transition hover:bg-rose-50">Reset demo data</button></div>
    </header>
    <p className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs leading-5 text-amber-950">Fictional demo accounts only. Reset replaces application records and users with demo seed data.</p>
    {error && <p role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
    {notice && <p role="status" className="rounded-xl border border-emerald-100 bg-emerald-50 p-3 text-xs text-emerald-800">{notice}</p>}
    <section className="grid gap-3 sm:grid-cols-2">
      <article className="enterprise-card flex items-center justify-between p-4"><div><p className="text-[10px] text-slate-500">Workspace accounts</p><b className="page-title mt-1 block text-2xl text-brand-navy">{users.length}</b></div><Users size={19} className="text-brand-blue" /></article>
      <article className="enterprise-card flex items-center justify-between p-4"><div><p className="text-[10px] text-slate-500">Active accounts</p><b className="page-title mt-1 block text-2xl text-brand-navy">{users.filter((user) => user.is_active).length}</b></div><ShieldCheck size={19} className="text-emerald-600" /></article>
    </section>
    <section className="enterprise-card overflow-hidden">
      <div className="flex items-center gap-3 border-b border-slate-100 px-5 py-4"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-brand-blue"><UserPlus size={18} /></span><div><h2 className="text-sm font-bold text-slate-800">Create account</h2><p className="mt-0.5 text-[10px] text-slate-500">Assign the correct role and optional regional or institution scope.</p></div></div>
      <form onSubmit={create} className="grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-3">
        <label className="text-[10px] font-semibold text-slate-500">Full name<input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className="mt-1 block h-10 w-full px-3 text-xs" /></label>
        <label className="text-[10px] font-semibold text-slate-500">Email address<input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-1 block h-10 w-full px-3 text-xs" /></label>
        <label className="text-[10px] font-semibold text-slate-500">Temporary password<input required minLength={8} type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="mt-1 block h-10 w-full px-3 text-xs" /></label>
        <label className="text-[10px] font-semibold text-slate-500">Role<select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="mt-1 block h-10 w-full px-3 text-xs">{['institution', 'regional_officer', 'bureau_officer', 'evc_committee', 'admin'].map((role) => <option key={role}>{role}</option>)}</select></label>
        <label className="text-[10px] font-semibold text-slate-500">Region<input value={form.region} onChange={(e) => setForm({ ...form, region: e.target.value })} className="mt-1 block h-10 w-full px-3 text-xs" /></label>
        <label className="text-[10px] font-semibold text-slate-500">Institution ID<input type="number" value={form.institution_id} onChange={(e) => setForm({ ...form, institution_id: e.target.value })} className="mt-1 block h-10 w-full px-3 text-xs" /></label>
        <button className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-brand-navy px-4 text-xs font-semibold text-white transition hover:bg-blue-900 sm:col-span-2 xl:col-span-3"><UserPlus size={15} />Create user</button>
      </form>
    </section>
    <section className="enterprise-card overflow-hidden">
      <div className="flex items-center gap-3 border-b border-slate-100 px-5 py-4"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50 text-violet-700"><Building2 size={18} /></span><div><h2 className="text-sm font-bold text-slate-800">Workspace accounts</h2><p className="mt-0.5 text-[10px] text-slate-500">Update role, region assignment or account availability.</p></div></div>
      <div className="overflow-x-auto"><table className="min-w-[850px] w-full text-left text-xs"><thead className="bg-slate-50/80 text-[10px] font-semibold uppercase tracking-wide text-slate-500"><tr>{['User', 'Role', 'Region', 'Institution', 'Status', 'Action'].map((x) => <th key={x} className="px-4 py-3">{x}</th>)}</tr></thead>
        <tbody className="divide-y divide-slate-100">{users.map((u) => <tr key={u.id} className="transition hover:bg-slate-50/70"><td className="px-4 py-3"><span className="font-semibold text-slate-800">{u.full_name}</span><span className="mt-0.5 block text-[10px] text-slate-500">{u.email}</span></td><td className="px-4 py-3"><select aria-label={`Role for ${u.full_name}`} value={u.role} onChange={(e) => apiPut(`/users/${u.id}`, { role: e.target.value }).then(load).catch((err: Error) => setError(err.message))} className="h-8 max-w-48 px-2 text-[10px]">{['institution', 'regional_officer', 'bureau_officer', 'evc_committee', 'admin'].map((role) => <option key={role}>{role}</option>)}</select></td><td className="px-4 py-3"><div className="flex items-center gap-1"><input aria-label={`Region for ${u.full_name}`} value={regions[u.id] ?? u.region ?? ''} onChange={(e) => setRegions({ ...regions, [u.id]: e.target.value })} onBlur={() => updateRegion(u.id)} className="h-8 w-24 px-2 text-[10px]" /><button onClick={() => updateRegion(u.id)} className="rounded px-2 py-1 text-[10px] font-semibold text-brand-blue hover:bg-blue-50">Save</button></div></td><td className="px-4 py-3 text-slate-500">{u.institution_id || '—'}</td><td className="px-4 py-3"><span className={`rounded-full px-2 py-1 text-[9px] font-semibold ${u.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>{u.is_active ? 'Active' : 'Inactive'}</span></td><td className="px-4 py-3"><button onClick={() => update(u, !u.is_active)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-[10px] font-semibold text-slate-600 transition hover:border-blue-200 hover:bg-blue-50 hover:text-brand-blue">{u.is_active ? 'Deactivate' : 'Activate'}</button></td></tr>)}</tbody>
      </table></div>
      {users.length === 0 && <p className="p-8 text-center text-xs text-slate-500">No accounts are available.</p>}
    </section>
  </div>;
}
