import { AlertCircle, Bell, Check, CheckCircle2, Clock3, Mail, MailCheck } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiGet, apiPost } from '../api/client';

type Notification = { id: number; event_type: string; related_id: string | null; message: string; created_at: string; due_date: string | null; is_read: boolean; action_link: string | null };

export default function Notifications() {
  const [items, setItems] = useState<Notification[]>([]);
  const [config, setConfig] = useState<{ email_configured: boolean } | null>(null);
  const [unread, setUnread] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    try { setItems(await apiGet<Notification[]>('/notifications', { unread_only: unread })); setError(''); }
    catch (err) { setError(err instanceof Error ? err.message : 'Unable to load notifications'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); apiGet<{ email_configured: boolean }>('/notifications/config').then(setConfig).catch(() => setConfig(null)); }, [unread]);

  async function markRead(id: number) {
    try { await apiPost(`/notifications/${id}/read`); await load(); window.dispatchEvent(new Event('nexora-notifications-updated')); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not mark as read'); }
  }

  const unreadCount = useMemo(() => items.filter((item) => !item.is_read).length, [items]);

  return <div className="space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Workspace activity</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">Notifications</h1><p className="mt-1 text-sm text-slate-500">Updates and reminders for records in your portfolio.</p></div><label className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[10px] font-semibold text-slate-600"><input type="checkbox" checked={unread} onChange={(event) => setUnread(event.target.checked)} className="h-4 w-4 accent-blue-600" />Unread only</label></header>
    <section className="grid gap-3 sm:grid-cols-3">
      <article className="enterprise-card flex items-center justify-between p-4"><div><p className="text-[10px] text-slate-500">Notifications in view</p><b className="page-title mt-2 block text-2xl text-brand-navy">{loading ? '—' : items.length}</b></div><Bell size={18} className="text-brand-blue" /></article>
      <article className="enterprise-card flex items-center justify-between p-4"><div><p className="text-[10px] text-slate-500">Unread updates</p><b className="page-title mt-2 block text-2xl text-brand-navy">{loading ? '—' : unreadCount}</b></div><AlertCircle size={18} className="text-amber-600" /></article>
      <article className="enterprise-card flex items-center justify-between p-4"><div><p className="text-[10px] text-slate-500">Delivery channel</p><b className="mt-2 block text-xs text-slate-700">{config?.email_configured ? 'In-app & email' : 'In-app only'}</b></div><Mail size={18} className="text-slate-400" /></article>
    </section>
    {error && <p role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
    <section className="enterprise-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="text-sm font-bold text-slate-800">{unread ? 'Unread updates' : 'Recent activity'}</h2><p className="mt-1 text-[10px] text-slate-500">Notifications are scoped to your account.</p></div><span className="flex items-center gap-1 text-[10px] text-slate-400"><CheckCircle2 size={14} />{unreadCount} unread</span></div>
      {loading ? <div className="space-y-3 p-5">{Array.from({ length: 4 }, (_, index) => <div key={index} className="h-20 animate-pulse rounded-lg bg-slate-100" />)}</div> : items.length === 0 ? <div className="p-12 text-center"><CheckCircle2 size={26} className="mx-auto text-emerald-500" /><p className="mt-3 text-sm font-semibold text-slate-700">You’re all caught up</p><p className="mt-1 text-xs text-slate-500">There are no notifications to display.</p></div> : <div className="divide-y divide-slate-100">{items.map((item) => <article key={item.id} className={`flex gap-3 p-5 transition hover:bg-slate-50/60 ${!item.is_read ? 'bg-blue-50/20' : ''}`}>
        <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${item.is_read ? 'bg-slate-100 text-slate-500' : 'bg-blue-50 text-brand-blue'}`}><Bell size={16} /></span>
        <div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><span className="text-[9px] font-bold uppercase tracking-wide text-brand-blue">{item.event_type.replace(/_/g, ' ')}</span>{!item.is_read && <span className="h-1.5 w-1.5 rounded-full bg-blue-600" />}</div><p className="mt-1 text-xs font-semibold text-slate-800">{item.message}</p><p className="mt-1 flex flex-wrap items-center gap-1.5 text-[10px] text-slate-500"><Clock3 size={12} />{new Date(item.created_at).toLocaleString()}{item.due_date && <span>· Due {new Date(item.due_date).toLocaleDateString()}</span>}</p></div>
        <div className="flex shrink-0 flex-col items-end gap-2">{item.action_link && <Link to={item.action_link} className="text-[10px] font-semibold text-brand-blue hover:underline">View record</Link>}{!item.is_read && <button onClick={() => void markRead(item.id)} className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-[9px] font-semibold text-slate-600 hover:bg-white"><Check size={12} />Mark read</button>}</div>
      </article>)}</div>}
    </section>
  </div>;
}
