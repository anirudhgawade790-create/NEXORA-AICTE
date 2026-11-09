import { AlertCircle, CheckCircle2, Clock3, ExternalLink, Globe2, RefreshCw, Search } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { useAuth } from '../auth/AuthContext';

type SyncStatus = {
  status: 'available' | 'degraded' | 'unavailable' | 'not_configured' | 'never_synced' | string;
  configured: boolean;
  record_count: number;
  last_attempt_at: string | null;
  last_success_at: string | null;
  last_error: string | null;
  sync_interval_minutes: number;
  source_name: string;
  source_url: string;
  onod_url: string;
  aicte_url: string;
};

type Institution = {
  record_type?: 'institution' | 'aggregate';
  aicte_id: string | null;
  name: string;
  state: string | null;
  district: string | null;
  city: string | null;
  address: string | null;
  approved_courses: string[];
  approval_status: string | null;
  academic_year: string | null;
  source_updated_at: string | null;
  synchronized_at: string;
  government_engineering_institutes_count?: number | string;
  approved_seats_count?: number | string;
};

type InstitutionResponse = { status: SyncStatus; total: number; records: Institution[] };

function formatDate(value: string | null) {
  if (!value) return 'Not available';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function statusStyle(status: SyncStatus['status']) {
  if (status === 'available') return 'bg-emerald-50 text-emerald-700';
  if (status === 'degraded') return 'bg-amber-50 text-amber-800';
  return 'bg-slate-100 text-slate-700';
}

function formatCount(value: number | string | undefined) {
  if (value === undefined || value === null || value === '') return 'Not provided';
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed.toLocaleString() : String(value);
}

export default function LiveAICTEData() {
  const { user } = useAuth();
  const [data, setData] = useState<InstitutionResponse | null>(null);
  const [search, setSearch] = useState('');
  const [submittedSearch, setSubmittedSearch] = useState('');
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const pageSize = 50;

  const loadData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const result = await apiGet<InstitutionResponse>('/aicte-data', {
        search: submittedSearch,
        limit: pageSize,
        offset,
      });
      setData(result);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load public AICTE data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [offset, submittedSearch]);

  useEffect(() => {
    void loadData();
    const timer = window.setInterval(() => { void loadData(true); }, 60_000);
    return () => window.clearInterval(timer);
  }, [loadData]);

  async function syncNow() {
    setRefreshing(true);
    try {
      await apiPost<SyncStatus>('/aicte-data/sync');
      await loadData(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Public data synchronization failed.');
      setRefreshing(false);
    }
  }

  const status = data?.status;
  const records = data?.records || [];
  const hasAggregateRecords = records.some((item) => item.record_type === 'aggregate');

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[.13em] text-brand-blue"><Globe2 size={14} /> Public source dashboard</div>
          <h1 className="page-title text-2xl font-bold text-brand-navy md:text-[28px]">AICTE public data</h1>
          <p className="mt-1 text-sm text-slate-500">Public source records only; internal workflow records are not included.</p>
        </div>
        <div className="flex gap-2">
          {user?.role === 'admin' && <button onClick={() => void syncNow()} disabled={refreshing || !status?.configured} className="inline-flex h-9 items-center gap-2 rounded-lg bg-brand-blue px-3 text-xs font-semibold text-white disabled:opacity-50"><RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />Sync now</button>}
          <button onClick={() => void loadData(true)} disabled={refreshing} className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600 disabled:opacity-50"><RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />Refresh</button>
        </div>
      </header>

      {error && <div role="alert" className="flex items-start gap-2 rounded-xl border border-rose-100 bg-rose-50 p-4 text-sm text-rose-700"><AlertCircle size={17} className="mt-0.5 shrink-0" />{error}</div>}

      {status && <section className="grid gap-3 md:grid-cols-3">
        <article className="enterprise-card p-4">
          <p className="text-xs font-medium text-slate-500">Source connection</p>
          <p className="mt-2"><span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${statusStyle(status.status)}`}>{status.status.replace(/_/g, ' ')}</span></p>
          <p className="mt-3 text-[11px] text-slate-500">{status.configured ? `${status.record_count.toLocaleString()} cached public records` : status.record_count ? `${status.record_count.toLocaleString()} cached records · source not connected` : 'No verified AICTE dataset/API configured'}</p>
        </article>
        <article className="enterprise-card p-4">
          <p className="text-xs font-medium text-slate-500">Last successful synchronization</p>
          <p className="mt-2 text-sm font-semibold text-slate-800">{formatDate(status.last_success_at)}</p>
          <p className="mt-3 inline-flex items-center gap-1 text-[11px] text-slate-500"><Clock3 size={13} />Automatic sync every {status.sync_interval_minutes} minutes when configured</p>
        </article>
        <article className="enterprise-card p-4">
          <p className="text-xs font-medium text-slate-500">Data publisher</p>
          <a href={status.source_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex items-center gap-1 text-sm font-semibold text-brand-blue hover:underline">{status.source_name}<ExternalLink size={13} /></a>
          <p className="mt-2 text-[11px] text-slate-500">Last sync attempt: {formatDate(status.last_attempt_at)}</p>
        </article>
      </section>}

      {status?.last_error && <div role="status" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900">Sync status: {status.last_error}</div>}

      {status && !status.configured && <section className="enterprise-card border-blue-100 bg-blue-50/60 p-5">
        <div className="flex items-start gap-3">
          <AlertCircle size={18} className="mt-0.5 shrink-0 text-brand-blue" />
          <div>
            <h2 className="text-sm font-bold text-slate-800">Public API not connected</h2>
            <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-600">No institution rows are being fabricated or imported from undocumented portal traffic. To enable public data, configure a verified AICTE dataset resource ID, API key and publisher page from the documented Open Government Data API. ONOD/dashboard access did not expose a documented public API contract during integration.</p>
            <div className="mt-3 flex flex-wrap gap-4 text-xs font-semibold">
              <a href={status.onod_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand-blue hover:underline">AICTE ONOD Portal <ExternalLink size={12} /></a>
              <a href={status.aicte_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand-blue hover:underline">AICTE official website <ExternalLink size={12} /></a>
              <a href="https://data.gov.in/apis" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand-blue hover:underline">OGD API documentation <ExternalLink size={12} /></a>
            </div>
          </div>
        </div>
      </section>}

      <section className="enterprise-card overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
          <div><h2 className="text-sm font-bold text-slate-800">{hasAggregateRecords ? 'Year-wise published totals' : 'Cached public institution records'}</h2><p className="mt-1 text-[11px] text-slate-500">{hasAggregateRecords ? 'Historical totals from the selected dataset; these are not individual institution records or current approval status.' : 'Source-provided institution identifiers, location, courses and approval fields only'}</p></div>
          <form onSubmit={(event) => { event.preventDefault(); setOffset(0); setSubmittedSearch(search.trim()); }} className="flex gap-2">
            <label className="relative"><span className="sr-only">Search public data</span><Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={hasAggregateRecords ? 'Search dataset' : 'Search institutions'} className="h-9 w-52 pl-9 pr-3 text-xs" /></label>
            <button type="submit" className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600">Search</button>
          </form>
        </div>
        {loading ? <div className="space-y-3 p-5">{Array.from({ length: 5 }, (_, index) => <div key={index} className="h-10 animate-pulse rounded-lg bg-slate-100" />)}</div> : <div className="overflow-x-auto">
          <table className="min-w-[700px] w-full text-left text-xs">
            {hasAggregateRecords ? <>
              <thead className="bg-slate-50 text-[10px] uppercase tracking-wide text-slate-500"><tr>{['Academic year', 'Government engineering institutes', 'Approved seats'].map((label) => <th key={label} className="px-4 py-3 font-semibold">{label}</th>)}</tr></thead>
              <tbody className="divide-y divide-slate-100">{records.map((item, index) => <tr key={`${item.academic_year || item.name}-${index}`} className="hover:bg-slate-50/70">
                <td className="px-4 py-3 font-semibold text-slate-800">{item.academic_year || 'Not provided'}</td>
                <td className="px-4 py-3 text-slate-600">{formatCount(item.government_engineering_institutes_count)}</td>
                <td className="px-4 py-3 text-slate-600">{formatCount(item.approved_seats_count)}</td>
              </tr>)}</tbody>
            </> : <>
              <thead className="bg-slate-50 text-[10px] uppercase tracking-wide text-slate-500"><tr>{['AICTE ID', 'Institution', 'Location', 'Approved courses', 'Approval status', 'Academic year', 'Source updated'].map((label) => <th key={label} className="px-4 py-3 font-semibold">{label}</th>)}</tr></thead>
              <tbody className="divide-y divide-slate-100">{records.map((item, index) => <tr key={`${item.aicte_id || item.name}-${index}`} className="hover:bg-slate-50/70">
                <td className="px-4 py-3 font-mono text-slate-600">{item.aicte_id || 'Not provided by source'}</td>
                <td className="max-w-64 px-4 py-3 font-semibold text-slate-800">{item.name}</td>
                <td className="px-4 py-3 text-slate-600">{[item.city, item.district, item.state].filter(Boolean).join(', ') || 'Not provided'}</td>
                <td className="max-w-72 px-4 py-3 text-slate-600">{item.approved_courses.length ? item.approved_courses.join(', ') : 'Not provided'}</td>
                <td className="px-4 py-3 text-slate-600">{item.approval_status || 'Not provided'}</td>
                <td className="px-4 py-3 text-slate-600">{item.academic_year || 'Not provided'}</td>
                <td className="px-4 py-3 text-slate-600">{item.source_updated_at || 'Not provided'}</td>
              </tr>)}</tbody>
            </>}
          </table>
          {!records.length && <div className="flex flex-col items-center p-10 text-center">
            <CheckCircle2 size={24} className="text-slate-300" />
            <p className="mt-2 text-sm font-semibold text-slate-700">{status?.configured ? 'No matching public records' : data?.total ? 'No matching cached records' : 'No live public records available'}</p>
            <p className="mt-1 max-w-lg text-xs text-slate-500">{status?.configured ? 'The configured dataset returned no matching records.' : data?.total ? 'A previously synchronized cache exists, but no records match this search. Cached data is not live.' : 'The public data source is not configured. NEXORA prototype institutions are intentionally excluded from this dashboard.'}</p>
          </div>}
        </div>}
        {data && data.total > pageSize && <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3 text-xs text-slate-500">
          <span>{offset + 1}–{Math.min(offset + pageSize, data.total)} of {data.total.toLocaleString()}</span>
          <div className="flex gap-2"><button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - pageSize))} className="rounded border border-slate-200 px-3 py-1.5 disabled:opacity-40">Previous</button><button disabled={offset + pageSize >= data.total} onClick={() => setOffset(offset + pageSize)} className="rounded border border-slate-200 px-3 py-1.5 disabled:opacity-40">Next</button></div>
        </div>}
      </section>

      <p className="text-[11px] text-slate-500">Internal application tracking, pending stages, EVC appointments, compliance/undertakings, and document expiry are NEXORA prototype records. They are not represented as official AICTE status without an authorized data-sharing API.</p>
    </div>
  );
}
