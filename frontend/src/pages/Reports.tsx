import { ArrowDownToLine, BarChart3, FileBarChart2, FileCheck2, Landmark, ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import { apiDownload } from '../api/client';

const reports = [
  ['applications-pendency', 'Application pendency', 'Applications in progress, workflow stage and elapsed days', FileBarChart2],
  ['region-performance', 'Regional performance', 'Processing volume and average timeline by region', BarChart3],
  ['evc', 'EVC appointments', 'Scheduled and completed evaluation visits', Landmark],
  ['compliance', 'Compliance register', 'Institution undertakings and verification status', ShieldCheck],
  ['documents', 'Document validity', 'Supporting records and expiry information', FileCheck2],
  ['overdue', 'Overdue actions', 'Escalations and overdue application actions', BarChart3],
  ['decisions', 'Application decisions', 'Recorded application decisions and outcomes', FileBarChart2],
] as const;

export default function Reports() {
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ region: '', status: '', stage: '' });

  async function download(key: string) {
    setBusy(key);
    setError('');
    try { await apiDownload(`/reports/${key}.csv`, filters); }
    catch (err) { setError(err instanceof Error ? err.message : 'Report download failed'); }
    finally { setBusy(''); }
  }

  return <div className="space-y-6">
    <header><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Analytics &amp; exports</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">Reports &amp; analytics</h1><p className="mt-1 text-sm text-slate-500">Export data within the access scope of your account.</p></header>
    <section className="enterprise-card flex flex-wrap items-end gap-3 p-4">
      <div className="mr-auto"><h2 className="text-xs font-bold text-slate-700">Report filters</h2><p className="mt-1 text-[10px] text-slate-500">Applied to reports that support these dimensions.</p></div>
      <label className="text-[10px] font-medium text-slate-500">Region<select aria-label="Report region filter" value={filters.region} onChange={(event) => setFilters({ ...filters, region: event.target.value })} className="mt-1 block h-9 min-w-32 px-3 text-xs"><option value="">All regions</option>{['North', 'South', 'East', 'West', 'Central'].map((region) => <option key={region}>{region}</option>)}</select></label>
      <label className="text-[10px] font-medium text-slate-500">Status<select aria-label="Report status filter" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })} className="mt-1 block h-9 min-w-32 px-3 text-xs"><option value="">All statuses</option>{['pending', 'returned', 'approved', 'rejected'].map((status) => <option key={status}>{status}</option>)}</select></label>
      <label className="text-[10px] font-medium text-slate-500">Workflow stage<select aria-label="Report stage filter" value={filters.stage} onChange={(event) => setFilters({ ...filters, stage: event.target.value })} className="mt-1 block h-9 min-w-40 px-3 text-xs"><option value="">All stages</option>{['submission', 'initial_scrutiny', 'deficiency_check', 'evc_scheduling', 'evc_completion', 'committee_stage', 'authorised_decision', 'final_status'].map((stage) => <option key={stage} value={stage}>{stage.replace(/_/g, ' ')}</option>)}</select></label>
    </section>
    {error && <p role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {reports.map(([key, title, description, Icon]) => <article key={key} className="enterprise-card group flex min-h-40 flex-col justify-between p-5 transition hover:-translate-y-0.5 hover:border-blue-100 hover:shadow-lg">
        <div className="flex items-start justify-between gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-brand-blue"><Icon size={19} /></span><span className="rounded-md bg-slate-50 px-2 py-1 text-[9px] font-semibold uppercase tracking-wide text-slate-500">CSV</span></div>
        <div className="mt-5 flex items-end justify-between gap-2"><div><h2 className="text-xs font-bold text-slate-800">{title}</h2><p className="mt-1 max-w-xs text-[10px] leading-4 text-slate-500">{description}</p></div><button disabled={Boolean(busy)} onClick={() => void download(key)} aria-label={`Download ${title}`} className="flex h-9 shrink-0 items-center gap-2 rounded-lg bg-brand-navy px-3 text-[10px] font-semibold text-white transition hover:bg-blue-900 disabled:opacity-50">{busy === key ? 'Preparing…' : <><ArrowDownToLine size={14} />Export</>}</button></div>
      </article>)}
    </section>
  </div>;
}
