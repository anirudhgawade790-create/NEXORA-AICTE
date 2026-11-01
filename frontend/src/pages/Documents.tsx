import { AlertCircle, Download, FileCheck2, FileText, LockKeyhole, ShieldCheck, UploadCloud } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiDownload, apiGet, apiPost } from '../api/client';
import { useAuth } from '../auth/AuthContext';

type DocumentItem = { id: number; application_id: string | null; category: string; file_name: string; status: string; expiry_date: string | null; file_size: number; ocr_text?: string | null; ocr_summary?: string | null };
const categories = ['Lease Documents', 'Land and Building Documents', 'Institutional Undertakings', 'Approval Supporting Documents', 'Compliance Evidence', 'Other Prescribed Documents'];
const documentStatCards: { label: string; key: 'total' | 'pending' | 'verified' | 'expired'; icon: LucideIcon; style: string }[] = [
  { label: 'Documents in view', key: 'total', icon: FileText, style: 'text-brand-blue bg-blue-50' },
  { label: 'Awaiting verification', key: 'pending', icon: AlertCircle, style: 'text-amber-700 bg-amber-50' },
  { label: 'Verified', key: 'verified', icon: ShieldCheck, style: 'text-emerald-700 bg-emerald-50' },
  { label: 'Expired', key: 'expired', icon: FileCheck2, style: 'text-rose-700 bg-rose-50' },
];

function statusTone(value: string) {
  if (value === 'verified') return 'bg-emerald-50 text-emerald-700';
  if (value === 'deficient' || value === 'rejected' || value === 'expired') return 'bg-rose-50 text-rose-700';
  if (value === 'under_verification') return 'bg-amber-50 text-amber-700';
  return 'bg-slate-100 text-slate-600';
}

export default function Documents() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [items, setItems] = useState<DocumentItem[]>([]);
  const [category, setCategory] = useState(categories[0]);
  const [applicationId, setApplicationId] = useState(() => searchParams.get('application_id') || '');
  const [file, setFile] = useState<File | null>(null);
  const [remarks, setRemarks] = useState<Record<number, string>>({});
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const institution = user?.role === 'institution';
  const canVerify = ['admin', 'regional_officer', 'bureau_officer'].includes(user?.role || '');

  async function load() {
    try { setItems(await apiGet<DocumentItem[]>('/documents', { application_id: applicationId })); setError(''); }
    catch (err) { setError(err instanceof Error ? err.message : 'Unable to load documents'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);

  async function upload(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    if (!['application/pdf', 'image/jpeg', 'image/png'].includes(file.type) || file.size > 10 * 1024 * 1024) {
      setError('Choose a PDF, JPG or PNG file no larger than 10 MB.');
      return;
    }
    const form = new FormData();
    form.append('file', file);
    form.append('category', category);
    if (applicationId) form.append('application_id', applicationId);
    setBusy(true);
    try { await apiPost('/documents', form); setFile(null); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Upload failed'); }
    finally { setBusy(false); }
  }

  async function verify(id: number, status: string) {
    if (!remarks[id]?.trim()) { setError('Please enter review remarks before updating document status.'); return; }
    try { await apiPost(`/documents/${id}/verify`, { status, remarks: remarks[id].trim() }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Verification failed'); }
  }

  const counts = useMemo(() => ({
    total: items.length,
    pending: items.filter((item) => item.status === 'under_verification').length,
    verified: items.filter((item) => item.status === 'verified').length,
    expired: items.filter((item) => item.status === 'expired').length,
  }), [items]);

  return <div className="space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Records &amp; evidence</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">Document management</h1><p className="mt-1 text-sm text-slate-500">Secure records, verification status and validity tracking.</p></div><span className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[10px] text-slate-500"><LockKeyhole size={14} className="text-emerald-600" />Private, role-scoped access</span></header>
    {error && <p role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}

    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {documentStatCards.map(({ label, key, icon: Icon, style }) => <article key={label} className="enterprise-card flex items-center justify-between p-4"><div><p className="text-[10px] text-slate-500">{label}</p><p className="page-title mt-2 text-2xl font-bold text-brand-navy">{loading ? '—' : counts[key]}</p></div><span className={`flex h-10 w-10 items-center justify-center rounded-xl ${style}`}><Icon size={18} /></span></article>)}
    </section>

    <div className="grid gap-5 xl:grid-cols-[.8fr_1.2fr]">
      {institution && <form onSubmit={upload} className="enterprise-card h-fit overflow-hidden">
        <div className="border-b border-slate-100 bg-slate-50/60 px-5 py-4"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-brand-blue"><UploadCloud size={18} /></span><div><h2 className="text-sm font-bold text-slate-800">Upload a document</h2><p className="text-[10px] text-slate-500">PDF, JPG or PNG · up to 10 MB</p></div></div></div>
        <div className="space-y-4 p-5">
          <label className="block text-[10px] font-semibold text-slate-600">Document category<select value={category} onChange={(event) => setCategory(event.target.value)} className="mt-1.5 h-10 w-full px-3 text-xs">{categories.map((value) => <option key={value}>{value}</option>)}</select></label>
          <label className="block text-[10px] font-semibold text-slate-600">Application ID <span className="font-normal text-slate-400">(optional)</span><input value={applicationId} onChange={(event) => setApplicationId(event.target.value)} className="mt-1.5 h-10 w-full px-3 text-xs" placeholder="APP-YYYY-NNNN" /></label>
          <label className="flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-4 text-center transition hover:border-blue-300 hover:bg-blue-50/40"><UploadCloud size={23} className="text-slate-400" /><span className="mt-2 text-xs font-semibold text-slate-700">{file ? file.name : 'Choose a file to upload'}</span><span className="mt-1 text-[10px] text-slate-400">{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'PDF, JPG or PNG · Maximum 10 MB'}</span><input required type="file" accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png" onChange={(event) => setFile(event.target.files?.[0] || null)} className="sr-only" /></label>
          <button disabled={busy || !file} className="h-10 w-full rounded-lg bg-brand-blue text-xs font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50">{busy ? 'Uploading…' : 'Upload securely'}</button>
          <p className="text-[10px] leading-5 text-slate-400">Text extraction, when available, is advisory and does not determine authenticity or fraud.</p>
        </div>
      </form>}

      <section className="enterprise-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="text-sm font-bold text-slate-800">Document register</h2><p className="mt-1 text-[10px] text-slate-500">Download and review permitted records.</p></div><span className="text-[10px] text-slate-400">{loading ? 'Loading…' : `${items.length} records`}</span></div>
        {loading ? <div className="space-y-3 p-5">{Array.from({ length: 4 }, (_, index) => <div key={index} className="h-20 animate-pulse rounded-lg bg-slate-100" />)}</div> : items.length === 0 ? <div className="p-12 text-center"><FileText size={25} className="mx-auto text-slate-300" /><p className="mt-3 text-sm font-semibold text-slate-700">No documents found</p><p className="mt-1 text-xs text-slate-500">Available records will appear here.</p></div> : <div className="divide-y divide-slate-100">{items.map((item) => <article key={item.id} className="p-4 transition hover:bg-slate-50/50">
          <div className="flex flex-wrap items-start justify-between gap-3"><div className="flex min-w-0 items-start gap-3"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500"><FileText size={17} /></span><div className="min-w-0"><h3 className="truncate text-xs font-semibold text-slate-800">{item.file_name}</h3><p className="mt-1 text-[10px] text-slate-500">{item.category} · {item.application_id || 'Institution file'}{item.expiry_date ? ` · Expires ${new Date(item.expiry_date).toLocaleDateString()}` : ''}</p>{item.ocr_summary && <p className="mt-2 rounded-md bg-amber-50 px-2 py-1 text-[10px] text-amber-800">{item.ocr_summary}</p>}</div></div>
            <div className="flex shrink-0 items-center gap-2"><span className={`rounded-full px-2.5 py-1 text-[9px] font-semibold ${statusTone(item.status)}`}>{item.status.replace(/_/g, ' ')}</span><button aria-label={`Download ${item.file_name}`} onClick={() => apiDownload(`/documents/${item.id}/file`).catch((err: Error) => setError(err.message))} className="rounded-lg border border-slate-200 p-2 text-slate-500 transition hover:bg-white hover:text-brand-blue"><Download size={14} /></button></div>
          </div>
          {canVerify && item.status === 'under_verification' && <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto_auto_auto]"><input aria-label="Verification remarks" placeholder="Review remarks (required)" value={remarks[item.id] || ''} onChange={(event) => setRemarks({ ...remarks, [item.id]: event.target.value })} className="h-9 px-3 text-[10px]" />{['verified', 'deficient', 'rejected'].map((status) => <button key={status} disabled={!remarks[item.id]?.trim()} onClick={() => void verify(item.id, status)} className={`rounded-lg px-3 py-2 text-[10px] font-semibold capitalize disabled:opacity-40 ${status === 'verified' ? 'bg-emerald-600 text-white hover:bg-emerald-700' : status === 'deficient' ? 'bg-amber-50 text-amber-800 hover:bg-amber-100' : 'bg-rose-50 text-rose-700 hover:bg-rose-100'}`}>{status}</button>)}</div>}
        </article>)}</div>}
      </section>
    </div>
  </div>;
}
