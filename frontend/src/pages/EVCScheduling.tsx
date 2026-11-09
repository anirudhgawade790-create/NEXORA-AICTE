import { CalendarDays, CalendarPlus, CheckCircle2, Clock3, MapPin, SearchCheck, Users } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiGet, apiPost } from '../api/client';
import { useAuth } from '../auth/AuthContext';

type Appointment = { id: number; application_id: string; scheduled_date: string; location: string; status: string; findings?: string };
type EVCApplication = { id: string; current_stage: string; deadline: string | null };

export default function EVCScheduling() {
  const { user } = useAuth();
  const [items, setItems] = useState<Appointment[]>([]);
  const [apps, setApps] = useState<EVCApplication[]>([]);
  const [form, setForm] = useState({ application_id: '', scheduled_date: '', location: '' });
  const [completion, setCompletion] = useState<Record<number, { findings: string; recommendation: string }>>({});
  const [view, setView] = useState<'table' | 'calendar'>('calendar');
  const [filters, setFilters] = useState({ start_date: '', end_date: '', status: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const [appointments, applications] = await Promise.all([
        apiGet<Appointment[]>('/evc', filters), apiGet<EVCApplication[]>('/applications'),
      ]);
      setItems(appointments);
      setApps(applications.filter((item) => ['evc_scheduling', 'evc_completion'].includes(item.current_stage)));
      setError('');
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to load EVC data'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [filters]);

  async function schedule(event: React.FormEvent) {
    event.preventDefault();
    try { await apiPost('/evc', { ...form, scheduled_date: new Date(form.scheduled_date).toISOString(), committee_members: [] }); setForm({ application_id: '', scheduled_date: '', location: '' }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Scheduling failed'); }
  }
  async function complete(id: number) {
    try { await apiPost(`/evc/${id}/complete`, completion[id]); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Completion failed'); }
  }

  const counts = useMemo(() => ({
    scheduled: items.filter((item) => item.status === 'scheduled').length,
    completed: items.filter((item) => item.status === 'completed').length,
    queue: apps.filter((item) => item.current_stage === 'evc_scheduling').length,
    overdueStages: apps.filter((item) => item.deadline && new Date(item.deadline) < new Date()).length,
    overdueVisits: items.filter((item) => item.status === 'scheduled' && new Date(item.scheduled_date) < new Date()).length,
  }), [items, apps]);
  const canSchedule = ['admin', 'regional_officer', 'bureau_officer', 'evc_committee'].includes(user?.role || '');

  return <div className="space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Field operations</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">EVC scheduling</h1><p className="mt-1 text-sm text-slate-500">Coordinate evaluation visits and record committee outcomes.</p></div><div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[10px] text-slate-500"><CalendarDays size={15} className="text-brand-blue" />Visits &amp; inspections</div></header>
    {error && <p role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}

    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {[
        { label: 'Scheduled visits', value: counts.scheduled, icon: CalendarDays, tone: 'bg-blue-50 text-blue-700' },
        { label: 'Completed visits', value: counts.completed, icon: CheckCircle2, tone: 'bg-emerald-50 text-emerald-700' },
        { label: 'Awaiting scheduling', value: counts.queue, icon: Clock3, tone: 'bg-amber-50 text-amber-700' },
        { label: 'Overdue EVC stages', value: counts.overdueStages, icon: Clock3, tone: 'bg-rose-50 text-rose-700' },
        { label: 'Missed visit dates', value: counts.overdueVisits, icon: Clock3, tone: 'bg-orange-50 text-orange-700' },
      ].map((card) => <article key={card.label} className="enterprise-card flex items-center justify-between p-4"><div><p className="text-[11px] text-slate-500">{card.label}</p><p className="page-title mt-2 text-2xl font-bold text-brand-navy">{loading ? '—' : card.value}</p></div><span className={`flex h-10 w-10 items-center justify-center rounded-xl ${card.tone}`}><card.icon size={19} /></span></article>)}
    </section>

    {(counts.overdueStages > 0 || counts.overdueVisits > 0) && <section className="enterprise-card border-rose-200 p-5">
      <h2 className="text-sm font-bold text-rose-800">EVC actions needing attention</h2>
      <p className="mt-1 text-[10px] leading-5 text-rose-700">Overdue EVC deadlines and missed scheduled visits are escalated to configured officials. These example timelines are configurable and are not official AICTE rules.</p>
      <ul className="mt-3 space-y-2">
        {apps.filter((app) => app.deadline && new Date(app.deadline) < new Date()).map((app) => <li key={app.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-rose-50 px-3 py-2 text-[10px]">
          <Link to={`/applications/${app.id}`} className="font-semibold text-brand-blue hover:underline">{app.id} · {app.current_stage.replace(/_/g, ' ')}</Link>
          <span className="text-rose-700">Stage deadline {new Date(app.deadline!).toLocaleString()}</span>
        </li>)}
        {items.filter((item) => item.status === 'scheduled' && new Date(item.scheduled_date) < new Date()).map((item) => <li key={`visit-${item.id}`} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-orange-50 px-3 py-2 text-[10px]">
          <span className="font-semibold text-slate-700">{item.application_id} · Scheduled visit</span>
          <span className="text-orange-700">Visit date {new Date(item.scheduled_date).toLocaleString()}</span>
        </li>)}
      </ul>
    </section>}

    {canSchedule && <form onSubmit={schedule} className="enterprise-card p-5">
      <div className="mb-4 flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-brand-blue"><CalendarPlus size={18} /></span><div><h2 className="text-sm font-bold text-slate-800">Schedule an evaluation visit</h2><p className="text-[10px] text-slate-500">Select an application in the EVC workflow.</p></div></div>
      <div className="grid gap-3 md:grid-cols-3">
        <label className="text-[10px] font-semibold text-slate-600">Application<select required value={form.application_id} onChange={(event) => setForm({ ...form, application_id: event.target.value })} className="mt-1.5 h-10 w-full px-3 text-xs"><option value="">Select an application</option>{apps.map((app) => <option key={app.id} value={app.id}>{app.id} · {app.current_stage.replace(/_/g, ' ')}</option>)}</select></label>
        <label className="text-[10px] font-semibold text-slate-600">Visit date &amp; time<input required type="datetime-local" value={form.scheduled_date} onChange={(event) => setForm({ ...form, scheduled_date: event.target.value })} className="mt-1.5 h-10 w-full px-3 text-xs" /></label>
        <label className="text-[10px] font-semibold text-slate-600">Location<input required value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} placeholder="Visit venue" className="mt-1.5 h-10 w-full px-3 text-xs" /></label>
      </div>
      <div className="mt-4 flex justify-end"><button className="inline-flex h-9 items-center gap-2 rounded-lg bg-brand-blue px-4 text-xs font-semibold text-white transition hover:bg-blue-700"><CalendarPlus size={14} />Schedule visit</button></div>
    </form>}

    <section className="enterprise-card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-5 py-4">
        <div><h2 className="text-sm font-bold text-slate-800">Visit schedule</h2><p className="mt-1 text-[10px] text-slate-500">Appointments visible to your account</p></div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="sr-only" htmlFor="evc-status">Status</label><select id="evc-status" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })} className="h-9 px-3 text-[10px]"><option value="">All statuses</option><option value="scheduled">Scheduled</option><option value="completed">Completed</option><option value="cancelled">Cancelled</option></select>
          <input aria-label="Filter visits from date" type="date" value={filters.start_date} onChange={(event) => setFilters({ ...filters, start_date: event.target.value })} className="h-9 px-2 text-[10px]" />
          <input aria-label="Filter visits to date" type="date" value={filters.end_date} onChange={(event) => setFilters({ ...filters, end_date: event.target.value })} className="h-9 px-2 text-[10px]" />
          <div className="flex rounded-lg border border-slate-200 p-0.5"><button onClick={() => setView('calendar')} className={`rounded-md px-2.5 py-1.5 text-[10px] font-medium ${view === 'calendar' ? 'bg-brand-navy text-white' : 'text-slate-500'}`}>Cards</button><button onClick={() => setView('table')} className={`rounded-md px-2.5 py-1.5 text-[10px] font-medium ${view === 'table' ? 'bg-brand-navy text-white' : 'text-slate-500'}`}>Table</button></div>
        </div>
      </div>
      {loading ? <div className="grid gap-3 p-5 sm:grid-cols-2 lg:grid-cols-3">{Array.from({ length: 3 }, (_, index) => <div key={index} className="h-36 animate-pulse rounded-xl bg-slate-100" />)}</div> : items.length === 0 ? <div className="p-12 text-center"><SearchCheck size={26} className="mx-auto text-slate-300" /><p className="mt-3 text-sm font-semibold text-slate-700">No visits match this view</p><p className="mt-1 text-xs text-slate-500">Scheduled EVC appointments will appear here.</p></div> : view === 'calendar' ?
        <div className="grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-3">{items.map((item) => <article key={item.id} className="rounded-xl border border-slate-200 p-4 transition hover:border-blue-200 hover:shadow-md">
          <div className="flex items-start justify-between gap-3"><div className="flex items-center gap-3"><span className="flex h-11 w-11 flex-col items-center justify-center rounded-lg bg-blue-50 text-brand-blue"><span className="text-[8px] font-bold uppercase">{new Date(item.scheduled_date).toLocaleDateString(undefined, { month: 'short' })}</span><b className="text-sm leading-tight">{new Date(item.scheduled_date).getDate()}</b></span><div><p className="text-xs font-bold text-slate-800">{item.application_id}</p><p className="mt-0.5 text-[10px] text-slate-500">{new Date(item.scheduled_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p></div></div><span className={`rounded-full px-2 py-1 text-[9px] font-semibold capitalize ${item.status === 'completed' ? 'bg-emerald-50 text-emerald-700' : item.status === 'cancelled' ? 'bg-rose-50 text-rose-700' : 'bg-blue-50 text-blue-700'}`}>{item.status}</span></div>
          <p className="mt-4 flex items-center gap-2 border-t border-slate-100 pt-3 text-[10px] text-slate-600"><MapPin size={13} className="text-slate-400" />{item.location}</p>
          <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-500"><Users size={13} className="text-slate-400" />Evaluation committee</div>
          {item.status === 'scheduled' && user?.role === 'evc_committee' && <div className="mt-4 space-y-2 border-t border-slate-100 pt-3"><input aria-label={`Findings for ${item.application_id}`} placeholder="Visit findings" value={completion[item.id]?.findings || ''} onChange={(event) => setCompletion({ ...completion, [item.id]: { findings: event.target.value, recommendation: completion[item.id]?.recommendation || '' } })} className="h-9 w-full px-3 text-[10px]" /><input aria-label={`Recommendation for ${item.application_id}`} placeholder="Recommendation" value={completion[item.id]?.recommendation || ''} onChange={(event) => setCompletion({ ...completion, [item.id]: { findings: completion[item.id]?.findings || '', recommendation: event.target.value } })} className="h-9 w-full px-3 text-[10px]" /><button disabled={!completion[item.id]?.findings?.trim() || !completion[item.id]?.recommendation?.trim()} onClick={() => void complete(item.id)} className="w-full rounded-lg bg-emerald-600 px-3 py-2 text-[10px] font-semibold text-white hover:bg-emerald-700 disabled:opacity-40">Record visit outcome</button></div>}
          <Link to={`/applications/${item.application_id}`} className="mt-3 inline-flex items-center gap-1 text-[10px] font-semibold text-brand-blue hover:underline">View application <span aria-hidden="true">→</span></Link>
        </article>)}</div> :
        <div className="overflow-x-auto"><table className="min-w-[700px] w-full text-left text-xs"><thead className="bg-slate-50 text-[10px] uppercase tracking-wide text-slate-500"><tr>{['Application', 'Date & time', 'Location', 'Status', 'Committee action'].map((label) => <th key={label} className="px-4 py-3 font-semibold">{label}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{items.map((item) => <tr key={item.id}><td className="px-4 py-3"><Link to={`/applications/${item.application_id}`} className="font-semibold text-brand-blue">{item.application_id}</Link></td><td className="px-4 py-3 text-slate-600">{new Date(item.scheduled_date).toLocaleString()}</td><td className="px-4 py-3 text-slate-600">{item.location}</td><td className="px-4 py-3 capitalize">{item.status}</td><td className="min-w-64 px-4 py-3">{item.status === 'scheduled' && user?.role === 'evc_committee' && <div className="space-y-2"><input aria-label="Visit findings" placeholder="Findings" value={completion[item.id]?.findings || ''} onChange={(event) => setCompletion({ ...completion, [item.id]: { findings: event.target.value, recommendation: completion[item.id]?.recommendation || '' } })} className="h-8 w-full px-2 text-[10px]" /><input aria-label="Visit recommendation" placeholder="Recommendation" value={completion[item.id]?.recommendation || ''} onChange={(event) => setCompletion({ ...completion, [item.id]: { findings: completion[item.id]?.findings || '', recommendation: event.target.value } })} className="h-8 w-full px-2 text-[10px]" /><button disabled={!completion[item.id]?.findings?.trim() || !completion[item.id]?.recommendation?.trim()} onClick={() => void complete(item.id)} className="rounded-lg bg-emerald-600 px-3 py-1.5 text-[10px] font-semibold text-white disabled:opacity-40">Record outcome</button></div>}</td></tr>)}</tbody></table></div>}
    </section>
  </div>;
}
