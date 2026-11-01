import { Activity, CalendarClock, FileSearch, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';

type Audit = { id: number; user_id: number | null; action: string; affected_record_type: string; affected_record_id: string; previous_status: string | null; updated_status: string | null; reason: string | null; workflow_stage: string | null; timestamp: string };
export default function AuditLogs() {
  const [items, setItems] = useState<Audit[]>([]);
  const [recordType, setRecordType] = useState('');
  const [error, setError] = useState('');
  useEffect(() => { apiGet<Audit[]>('/audit-logs', { record_type: recordType }).then(setItems).catch((err: Error) => setError(err.message)); }, [recordType]);
  return <div className="space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Append-only activity history</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">Audit logs</h1><p className="mt-1 text-sm text-slate-500">Trace administrative and workflow changes across accessible records.</p></div>
      <span className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-600"><ShieldCheck size={15} className="text-emerald-600" />Read-only history</span>
    </header>
    <section className="grid gap-3 sm:grid-cols-2">
      <article className="enterprise-card flex items-center justify-between p-4"><div><p className="text-[10px] text-slate-500">Records in view</p><b className="page-title mt-1 block text-2xl text-brand-navy">{items.length}</b></div><Activity size={19} className="text-brand-blue" /></article>
      <article className="enterprise-card flex items-center justify-between p-4"><div><p className="text-[10px] text-slate-500">Record type filter</p><b className="mt-2 block text-xs font-semibold text-slate-700">{recordType || 'All record types'}</b></div><FileSearch size={19} className="text-slate-400" /></article>
    </section>
    <section className="enterprise-card flex flex-wrap items-end gap-3 p-4">
      <label className="text-[10px] font-semibold text-slate-500">Filter by record type<input value={recordType} onChange={(e) => setRecordType(e.target.value)} placeholder="All types" className="mt-1 block h-10 w-full min-w-56 px-3 text-xs" /></label>
      <span className="inline-flex items-center gap-1.5 pb-2 text-[10px] text-slate-400"><CalendarClock size={13} />Times shown in your local timezone</span>
    </section>
    {error && <p role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
    <section className="enterprise-card overflow-hidden">
      <div className="border-b border-slate-100 px-5 py-4"><h2 className="text-sm font-bold text-slate-800">Activity records</h2><p className="mt-1 text-[10px] text-slate-500">Audit entries are displayed as recorded and cannot be edited here.</p></div>
      <div className="overflow-x-auto"><table className="min-w-[1000px] w-full text-left text-xs">
        <thead className="bg-slate-50/80 text-[10px] font-semibold uppercase tracking-wide text-slate-500"><tr>{['Time', 'User', 'Action', 'Record', 'Previous', 'Updated', 'Reason', 'Stage'].map((heading) => <th key={heading} className="whitespace-nowrap px-4 py-3">{heading}</th>)}</tr></thead>
        <tbody className="divide-y divide-slate-100">{items.map((item) => <tr key={item.id} className="transition hover:bg-slate-50/70"><td className="whitespace-nowrap px-4 py-3 text-slate-500">{new Date(item.timestamp).toLocaleString()}</td><td className="px-4 py-3">{item.user_id ?? 'System'}</td><td className="px-4 py-3 font-semibold text-slate-700">{item.action}</td><td className="px-4 py-3">{item.affected_record_type} · {item.affected_record_id}</td><td className="px-4 py-3 text-slate-500">{item.previous_status || '—'}</td><td className="px-4 py-3 text-slate-500">{item.updated_status || '—'}</td><td className="max-w-64 px-4 py-3 text-slate-500">{item.reason || '—'}</td><td className="px-4 py-3 text-slate-500">{item.workflow_stage || '—'}</td></tr>)}</tbody>
      </table></div>
      {items.length === 0 && <div className="p-12 text-center"><Activity size={24} className="mx-auto text-slate-300" /><p className="mt-3 text-sm font-semibold text-slate-700">No audit records available</p><p className="mt-1 text-xs text-slate-500">Records will appear here when activity is recorded.</p></div>}
    </section>
  </div>;
}
