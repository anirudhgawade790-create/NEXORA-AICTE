import { ArrowDown, ArrowUp, Download, Plus, Search, SlidersHorizontal } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { apiDownload, apiGet } from '../api/client';
import { useAuth } from '../auth/AuthContext';

type ApplicationRow = { id: string; institution: string; region: string; type: string; submittedAt: string; stage: string; officer: string; daysPending: number; deadline: string | null; status: string };
const stages = ['submission', 'initial_scrutiny', 'deficiency_check', 'evc_scheduling', 'evc_completion', 'committee_stage', 'authorised_decision', 'final_status'];

function statusStyle(value: string) {
  if (['approved', 'completed', 'verified'].includes(value.toLowerCase())) return 'bg-emerald-50 text-emerald-700 ring-emerald-600/10';
  if (['rejected', 'overdue'].includes(value.toLowerCase())) return 'bg-rose-50 text-rose-700 ring-rose-600/10';
  if (['returned', 'deficient'].includes(value.toLowerCase())) return 'bg-amber-50 text-amber-700 ring-amber-600/10';
  return 'bg-blue-50 text-blue-700 ring-blue-600/10';
}

function formatLabel(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function ApplicationsList() {
  const { user } = useAuth();
  const [queryParams, setQueryParams] = useSearchParams();
  const [rows, setRows] = useState<ApplicationRow[]>([]);
  const [search, setSearch] = useState(queryParams.get('search') || '');
  const [status, setStatus] = useState('');
  const [stage, setStage] = useState('');
  const [region, setRegion] = useState('');
  const [type, setType] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [sortBy, setSortBy] = useState('submitted_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [page, setPage] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    setLoading(true);
    apiGet<ApplicationRow[]>('/applications', { search, status, current_stage: stage, region, application_type: type, start_date: startDate, end_date: endDate, sort_by: sortBy, sort_order: sortOrder, limit: 10, offset: page * 10 })
      .then((result) => { setRows(result); setError(''); })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [search, status, stage, region, type, startDate, endDate, sortBy, sortOrder, page]);

  function updateSearch(value: string) {
    setSearch(value);
    setPage(0);
    if (value) setQueryParams({ search: value }, { replace: true });
    else setQueryParams({}, { replace: true });
  }

  async function exportCsv() {
    setExporting(true);
    try { await apiDownload('/reports/applications-pendency.csv', { region, status, stage, application_type: type }); }
    catch (err) { setError(err instanceof Error ? err.message : 'Export failed'); }
    finally { setExporting(false); }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Application management</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">All applications</h1><p className="mt-1 text-sm text-slate-500">Review and track applications in your authorized portfolio.</p></div>
        <div className="flex gap-2">
          <button onClick={() => void exportCsv()} disabled={exporting} className="inline-flex h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600 transition hover:bg-slate-50 disabled:opacity-50"><Download size={15} />{exporting ? 'Exporting…' : 'Export CSV'}</button>
          {user?.role === 'institution' && <Link to="/applications/new" className="inline-flex h-10 items-center gap-2 rounded-lg bg-brand-blue px-4 text-xs font-semibold text-white transition hover:bg-blue-700"><Plus size={16} />New application</Link>}
        </div>
      </header>

      <section className="enterprise-card p-4">
        <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold text-slate-500"><SlidersHorizontal size={14} />Filter and search</div>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5">
          <label className="relative sm:col-span-2 xl:col-span-1"><span className="sr-only">Search applications</span><Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" /><input aria-label="Search applications" placeholder="Search ID or type" value={search} onChange={(event) => updateSearch(event.target.value)} className="h-9 w-full pl-9 pr-3 text-xs" /></label>
          <select aria-label="Filter by status" value={status} onChange={(event) => { setStatus(event.target.value); setPage(0); }} className="h-9 px-3 text-xs"><option value="">All statuses</option>{['pending', 'returned', 'approved', 'rejected'].map((value) => <option key={value}>{value}</option>)}</select>
          <select aria-label="Filter by stage" value={stage} onChange={(event) => { setStage(event.target.value); setPage(0); }} className="h-9 px-3 text-xs"><option value="">All stages</option>{stages.map((value) => <option key={value} value={value}>{formatLabel(value)}</option>)}</select>
          <select aria-label="Filter by region" value={region} onChange={(event) => { setRegion(event.target.value); setPage(0); }} className="h-9 px-3 text-xs"><option value="">All regions</option>{['North', 'South', 'East', 'West', 'Central'].map((value) => <option key={value}>{value}</option>)}</select>
          <input aria-label="Filter by type" placeholder="Application type" value={type} onChange={(event) => { setType(event.target.value); setPage(0); }} className="h-9 px-3 text-xs" />
          <label className="flex items-center gap-2 text-[10px] text-slate-500"><span>From</span><input aria-label="Start date" type="date" value={startDate} onChange={(event) => { setStartDate(event.target.value); setPage(0); }} className="h-9 min-w-0 flex-1 px-2 text-[10px]" /></label>
          <label className="flex items-center gap-2 text-[10px] text-slate-500"><span>To</span><input aria-label="End date" type="date" value={endDate} onChange={(event) => { setEndDate(event.target.value); setPage(0); }} className="h-9 min-w-0 flex-1 px-2 text-[10px]" /></label>
          <select aria-label="Sort applications by" value={sortBy} onChange={(event) => setSortBy(event.target.value)} className="h-9 px-3 text-xs"><option value="submitted_at">Sort: submission</option><option value="deadline">Sort: deadline</option><option value="status">Sort: status</option><option value="current_stage">Sort: stage</option></select>
          <button onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')} className="inline-flex h-9 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-xs font-medium text-slate-600 hover:bg-slate-50">{sortOrder === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />}{sortOrder === 'asc' ? 'Oldest first' : 'Newest first'}</button>
        </div>
      </section>

      {error && <p role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-4 text-sm text-rose-700">{error}</p>}

      <section className="enterprise-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="text-sm font-bold text-slate-800">Application register</h2><p className="mt-1 text-[11px] text-slate-500">Page {page + 1} · Sorted by {sortBy.replace('_', ' ')}</p></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-semibold text-slate-600">{loading ? 'Loading…' : `${rows.length} records`}</span></div>
        {loading ? <div className="space-y-3 p-5">{Array.from({ length: 5 }, (_, index) => <div key={index} className="h-11 animate-pulse rounded-lg bg-slate-100" />)}</div> : rows.length === 0 ? <div className="p-12 text-center"><div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-slate-100"><Search size={18} className="text-slate-400" /></div><p className="mt-3 text-sm font-semibold text-slate-700">No applications found</p><p className="mt-1 text-xs text-slate-500">Try changing your search or filters.</p></div> :
          <div className="overflow-x-auto"><table className="min-w-[1000px] w-full text-left text-xs">
            <thead className="bg-slate-50/80 text-[10px] uppercase tracking-wide text-slate-500"><tr>{['Application ID', 'Institution', 'Region', 'Type', 'Current stage', 'Assigned officer', 'Submitted', 'Days pending', 'Status', ''].map((heading, index) => <th key={`${heading}-${index}`} className="whitespace-nowrap px-4 py-3 font-semibold">{heading}</th>)}</tr></thead>
            <tbody className="divide-y divide-slate-100">{rows.map((item) => <tr key={item.id} className="transition hover:bg-blue-50/30">
              <td className="whitespace-nowrap px-4 py-3"><Link to={`/applications/${item.id}`} className="font-semibold text-brand-blue hover:underline">{item.id}</Link></td>
              <td className="max-w-56 truncate px-4 py-3 font-medium text-slate-700">{item.institution}</td><td className="px-4 py-3 text-slate-500">{item.region}</td><td className="px-4 py-3 text-slate-600">{item.type}</td>
              <td className="px-4 py-3 text-slate-600">{formatLabel(item.stage)}</td><td className="px-4 py-3 text-slate-600">{item.officer}</td>
              <td className="whitespace-nowrap px-4 py-3 text-slate-500">{item.submittedAt ? new Date(item.submittedAt).toLocaleDateString() : '—'}</td>
              <td className="px-4 py-3 text-slate-600">{item.daysPending} days</td><td className="px-4 py-3"><span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold capitalize ring-1 ring-inset ${statusStyle(item.status)}`}>{item.status}</span></td>
              <td className="px-4 py-3"><Link to={`/applications/${item.id}`} className="font-semibold text-slate-500 hover:text-brand-blue">View</Link></td>
            </tr>)}</tbody>
          </table></div>}
        <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3"><span className="text-[10px] text-slate-500">Showing {rows.length ? page * 10 + 1 : 0}–{page * 10 + rows.length}</span><div className="flex gap-2"><button disabled={page === 0 || loading} onClick={() => setPage(page - 1)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-[11px] font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40">Previous</button><button disabled={rows.length < 10 || loading} onClick={() => setPage(page + 1)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-[11px] font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40">Next</button></div></div>
      </section>
    </div>
  );
}
