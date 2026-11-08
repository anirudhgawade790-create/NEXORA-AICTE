import {
  Activity, AlertTriangle, ArrowDownRight, ArrowRight, ArrowUpRight, CalendarClock,
  CheckCircle2, Clock3, FileBarChart2, FileCheck2, Gauge, Landmark, RefreshCw,
  ShieldAlert, Sparkles, Users, X,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { Link } from 'react-router-dom';
import { apiDownload, apiGet } from '../api/client';
import { useAuth } from '../auth/AuthContext';

type DashboardData = {
  kpis: { label: string; value: number; change: string }[];
  statusDistribution: { name: string; value: number }[];
  regionPendency: { region: string; value: number }[];
  stageDistribution: { name: string; value: number }[];
  monthlyTrend: { month: string; applications: number }[];
  complianceCompletion: { name: string; percent: number }[];
  upcomingDeadlines: { id: number | string; kind: string; title: string; due_date: string }[];
  attentionQueue: { id: number | string; kind: string; title: string; due_date: string; status: string }[];
  attentionSummary?: { overdue: number; dueSoon: number };
};
type ApplicationRow = {
  id: string; institution: string; region: string; type: string; submittedAt: string;
  stage: string; officer: string; daysPending: number; deadline: string | null; status: string;
};
type ComplianceQueueItem = { id: number; description: string; due_date: string; status: string; application_id: string | null };

const chartColors = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#7c3aed', '#0891b2'];
const cardIcons = [FileBarChart2, Clock3, SearchIcon, CalendarClock, ShieldAlert, FileCheck2, AlertTriangle, CheckCircle2];
const cardAccents = [
  'bg-blue-50 text-blue-700', 'bg-amber-50 text-amber-700', 'bg-violet-50 text-violet-700',
  'bg-cyan-50 text-cyan-700', 'bg-emerald-50 text-emerald-700', 'bg-rose-50 text-rose-700',
  'bg-orange-50 text-orange-700', 'bg-teal-50 text-teal-700',
];

function SearchIcon() { return <Activity size={19} />; }

const dashboardTourSteps = [
  {
    target: '[data-tour="dashboard-kpis"]',
    title: 'Portfolio at a glance',
    description: 'These cards show the key counts for your accessible applications, review stages, and deadlines.',
  },
  {
    target: '[data-tour="status-chart"]',
    title: 'Application status',
    description: 'See how many applications are pending, returned, approved, or in another decision state.',
  },
  {
    target: '[data-tour="workflow-chart"]',
    title: 'Where applications are in the process',
    description: 'This chart shows how cases are distributed across scrutiny, EVC, committee, and decision stages.',
  },
  {
    target: '[data-tour="compliance-chart"]',
    title: 'Compliance progress',
    description: 'Check the percentage of requirements verified in each category. These are demo tracking indicators, not official approvals.',
  },
  {
    target: '[data-tour="priority-queue"]',
    title: 'Deadlines that need attention',
    description: 'Overdue items and upcoming deadlines appear here. Select Review to open the related application or compliance record.',
  },
  {
    target: '[data-tour="recent-applications"]',
    title: 'Find and review a case',
    description: 'Search recent applications, open a case to see its timeline, or export the list as CSV.',
  },
];

function DashboardTour({ step, onStepChange, onClose }: {
  step: number;
  onStepChange: (step: number) => void;
  onClose: () => void;
}) {
  const [position, setPosition] = useState<{ top: number; left: number; width: number; height: number } | null>(null);
  const activeStep = dashboardTourSteps[step];

  useEffect(() => {
    const target = document.querySelector<HTMLElement>(activeStep.target);
    if (!target) {
      setPosition(null);
      return undefined;
    }

    target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
    const updatePosition = () => {
      const rect = target.getBoundingClientRect();
      const padding = 8;
      const width = Math.min(window.innerWidth - 24, rect.width + padding * 2);
      const left = Math.max(12, Math.min(rect.left - padding, window.innerWidth - width - 12));
      setPosition({
        top: Math.max(8, rect.top - padding),
        left,
        width,
        height: Math.min(window.innerHeight - Math.max(8, rect.top - padding) - 8, rect.height + padding * 2),
      });
    };

    const timer = window.setTimeout(updatePosition, 250);
    window.addEventListener('resize', updatePosition);
    window.addEventListener('scroll', updatePosition, true);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition, true);
    };
  }, [activeStep]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'ArrowRight' && step < dashboardTourSteps.length - 1) onStepChange(step + 1);
      if (event.key === 'ArrowLeft' && step > 0) onStepChange(step - 1);
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose, onStepChange, step]);

  const tooltipWidth = Math.min(360, window.innerWidth - 32);
  const tooltipLeft = position
    ? Math.max(16, Math.min(position.left + position.width / 2 - tooltipWidth / 2, window.innerWidth - tooltipWidth - 16))
    : Math.max(16, (window.innerWidth - tooltipWidth) / 2);
  const tooltipTop = position
    ? position.top + position.height + 16 + 200 < window.innerHeight
      ? position.top + position.height + 16
      : Math.max(16, position.top - 216)
    : Math.max(24, (window.innerHeight - 230) / 2);

  return (
    <div className="fixed inset-0 z-[100]">
      <button type="button" aria-label="Skip dashboard tour" onClick={onClose} className="absolute inset-0 h-full w-full cursor-default bg-slate-950/65" />
      {position && (
        <div
          aria-hidden="true"
          className="pointer-events-none fixed rounded-xl border-2 border-blue-400 shadow-[0_0_0_9999px_rgba(2,6,23,0.65),0_0_0_6px_rgba(59,130,246,0.28)] transition-all duration-300"
          style={{ top: position.top, left: position.left, width: position.width, height: position.height }}
        />
      )}
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="dashboard-tour-title"
        className="fixed w-[min(360px,calc(100vw-32px))] rounded-2xl border border-slate-200 bg-white p-5 text-slate-800 shadow-2xl dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
        style={{ top: tooltipTop, left: tooltipLeft }}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[.15em] text-blue-600 dark:text-blue-400">Dashboard tour · {step + 1} of {dashboardTourSteps.length}</p>
            <h2 id="dashboard-tour-title" className="mt-1.5 text-base font-bold">{activeStep.title}</h2>
          </div>
          <button type="button" onClick={onClose} aria-label="Skip intro" className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200">
            <X size={17} />
          </button>
        </div>
        <p className="mt-2 text-xs leading-5 text-slate-600 dark:text-slate-300">{activeStep.description}</p>
        <div className="mt-4 flex items-center justify-between gap-3 border-t border-slate-100 pt-3 dark:border-slate-700">
          <button type="button" onClick={onClose} className="text-[11px] font-semibold text-slate-500 transition hover:text-slate-800 dark:text-slate-400 dark:hover:text-white">Skip intro</button>
          <div className="flex items-center gap-2">
            <button type="button" onClick={() => onStepChange(step - 1)} disabled={step === 0} className="rounded-lg border border-slate-200 px-3 py-2 text-[11px] font-semibold text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800">Back</button>
            <button type="button" onClick={() => step === dashboardTourSteps.length - 1 ? onClose() : onStepChange(step + 1)} className="rounded-lg bg-blue-600 px-3.5 py-2 text-[11px] font-semibold text-white shadow-sm transition hover:bg-blue-700">
              {step === dashboardTourSteps.length - 1 ? 'Finish tour' : 'Next'}
            </button>
          </div>
        </div>
        <div className="mt-3 flex gap-1" aria-hidden="true">
          {dashboardTourSteps.map((tourStep, index) => <span key={tourStep.target} className={`h-1 flex-1 rounded-full ${index <= step ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-700'}`} />)}
        </div>
      </section>
    </div>
  );
}

function formatStage(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusTone(value: string) {
  if (['approved', 'completed', 'verified'].includes(value.toLowerCase())) return 'bg-emerald-50 text-emerald-700';
  if (['rejected', 'overdue', 'expired'].includes(value.toLowerCase())) return 'bg-rose-50 text-rose-700';
  if (['returned', 'deficient'].includes(value.toLowerCase())) return 'bg-amber-50 text-amber-700';
  return 'bg-blue-50 text-blue-700';
}

function daysUntil(date: string) {
  const due = new Date(date);
  const today = new Date();
  due.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  return Math.round((due.getTime() - today.getTime()) / 86_400_000);
}

function ChartCard({ title, note, children, className = '', tourId }: { title: string; note: string; children: React.ReactNode; className?: string; tourId?: string }) {
  return <section data-tour={tourId} className={`enterprise-card p-5 ${className}`}>
    <div className="mb-4"><h2 className="text-sm font-bold text-slate-800">{title}</h2><p className="mt-1 text-[11px] text-slate-500">{note}</p></div>
    <div className="h-[240px] w-full">{children}</div>
  </section>;
}

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [applications, setApplications] = useState<ApplicationRow[]>([]);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ region: '', application_type: '', stage: '', status: '' });
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [tableSearch, setTableSearch] = useState('');
  const [exporting, setExporting] = useState(false);
  const [tourStep, setTourStep] = useState<number | null>(null);
  const closeTour = useCallback(() => {
    if (user) localStorage.setItem(`nexora-dashboard-tour:${user.id}`, 'completed');
    setTourStep(null);
  }, [user?.id]);
  const changeTourStep = useCallback((step: number) => setTourStep(step), []);

  useEffect(() => {
    if (loading || !user) return;
    const tourKey = `nexora-dashboard-tour:${user.id}`;
    if (!localStorage.getItem(tourKey)) setTourStep(0);
  }, [loading, user?.id]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const [summary, rows] = await Promise.all([
        apiGet<DashboardData>('/dashboard', filters),
        apiGet<ApplicationRow[]>('/applications', { ...filters, limit: 6, sort_by: 'submitted_at', sort_order: 'desc' }),
      ]);
      if (!summary.attentionQueue || !summary.attentionSummary) {
        const [queueApplications, complianceItems] = await Promise.all([
          apiGet<ApplicationRow[]>('/applications', { ...filters, limit: 500, sort_by: 'deadline', sort_order: 'asc' }),
          user?.role === 'evc_committee'
            ? Promise.resolve<ComplianceQueueItem[]>([])
            : apiGet<ComplianceQueueItem[]>('/compliance'),
        ]);
        const cutoff = Date.now() + 30 * 86_400_000;
        const candidates = [
          ...queueApplications
            .filter((item): item is ApplicationRow & { deadline: string } =>
              Boolean(item.deadline) && !['approved', 'rejected'].includes(item.status))
            .map((item) => ({ id: item.id, kind: 'Application', title: item.id, due_date: item.deadline, status: item.status })),
          ...complianceItems
            .filter((item) => item.status !== 'verified' && new Date(item.due_date).getTime() <= cutoff)
            .filter((item) => !filters.region || queueApplications.some((app) => app.id === item.application_id))
            .map((item) => ({ id: item.id, kind: 'Compliance', title: item.description, due_date: item.due_date, status: item.status })),
        ].filter((item) => new Date(item.due_date).getTime() <= cutoff);
        const overdue = candidates
          .filter((item) => new Date(item.due_date).getTime() < Date.now())
          .sort((left, right) => right.due_date.localeCompare(left.due_date));
        const upcoming = candidates
          .filter((item) => new Date(item.due_date).getTime() >= Date.now())
          .sort((left, right) => left.due_date.localeCompare(right.due_date));
        summary.attentionQueue = [...overdue.slice(0, 5), ...upcoming.slice(0, 5)];
        summary.attentionSummary = { overdue: overdue.length, dueSoon: upcoming.length };
      }
      setData(summary);
      setApplications(rows);
      setUpdatedAt(new Date());
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load dashboard data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filters, user?.role]);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => { void refresh(); }, 60_000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const visibleApplications = useMemo(() => {
    const query = tableSearch.toLowerCase().trim();
    if (!query) return applications;
    return applications.filter((item) => `${item.id} ${item.institution} ${item.type}`.toLowerCase().includes(query));
  }, [applications, tableSearch]);

  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    return hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  }, []);
  const attentionItems = data?.attentionQueue
    || data?.upcomingDeadlines.map((item) => ({ ...item, status: 'pending' }))
    || [];
  const overdueCount = data?.attentionSummary?.overdue
    ?? attentionItems.filter((item) => daysUntil(item.due_date) < 0).length;
  const dueSoonCount = data?.attentionSummary?.dueSoon ?? attentionItems.length;
  const attentionLabel = data?.attentionSummary
    ? overdueCount ? `${overdueCount} overdue` : dueSoonCount ? `${dueSoonCount} due soon` : 'On track'
    : attentionItems.length ? `${attentionItems.length} in queue` : 'On track';

  async function exportApplications() {
    setExporting(true);
    try { await apiDownload('/reports/applications-pendency.csv', filters); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not export applications'); }
    finally { setExporting(false); }
  }

  function deadlineLink(item: DashboardData['upcomingDeadlines'][number]) {
    if (/^application$/i.test(item.kind)) return `/applications/${encodeURIComponent(String(item.id))}`;
    if (/lease/i.test(item.title)) return '/lease';
    return '/compliance';
  }

  const tooltipStyle = { borderRadius: 10, border: '1px solid #e6eaf0', boxShadow: '0 8px 24px rgba(15,23,42,.08)', fontSize: 12 };

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[.13em] text-brand-blue"><Sparkles size={14} /> Executive overview</div>
          <h1 className="page-title text-2xl font-bold text-brand-navy md:text-[28px]">{greeting}, {user?.role === 'admin' ? 'Administrator' : user?.full_name.split(' ')[0]}</h1>
          <p className="mt-1 text-sm text-slate-500">NEXORA prototype workflow overview · not an official AICTE data feed.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="hidden text-right sm:block"><p className="text-xs font-semibold text-slate-700">{new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</p><p className="text-[10px] text-slate-400">{updatedAt ? `NEXORA DB refreshed ${updatedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Prototype records'}</p></div>
          <select aria-label="Region filter" value={filters.region} onChange={(event) => setFilters({ ...filters, region: event.target.value })} className="h-9 min-w-32 px-3 text-xs">
            <option value="">All regions</option>{['North', 'South', 'East', 'West', 'Central'].map((region) => <option key={region}>{region}</option>)}
          </select>
          <button onClick={() => void refresh()} disabled={refreshing} className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600 transition hover:border-blue-200 hover:text-brand-blue disabled:opacity-50"><RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />Refresh</button>
        </div>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {(data?.kpis || []).map((item, index) => {
          const Icon = cardIcons[index] || Gauge;
          const accent = cardAccents[index] || cardAccents[0];
          const change = item.change || '';
          const negative = /down|decrease|-/i.test(change);
          const trend = /up|down|increase|decrease|%/i.test(change);
          return <article key={item.label} data-tour={index === 0 ? 'dashboard-kpis' : undefined} className="enterprise-card group p-4 transition duration-200 hover:-translate-y-0.5 hover:border-blue-100 hover:shadow-lg">
            <div className="flex items-start justify-between gap-2"><p className="text-xs font-medium text-slate-500">{item.label}</p><span className={`flex h-9 w-9 items-center justify-center rounded-xl ${accent}`}><Icon size={18} /></span></div>
            <div className="mt-4 flex items-end justify-between gap-2"><strong className="page-title text-[30px] font-bold leading-none text-brand-navy">{loading ? '—' : item.value.toLocaleString()}</strong>{trend && <span className={`inline-flex items-center gap-1 text-[10px] font-semibold ${negative ? 'text-rose-600' : 'text-emerald-600'}`}>{negative ? <ArrowDownRight size={13} /> : <ArrowUpRight size={13} />}{change}</span>}</div>
            <p className="mt-2 text-[10px] text-slate-400">{change && !trend ? change : 'Current portfolio'}</p>
          </article>;
        })}
        {!loading && !data?.kpis.length && <div className="enterprise-card col-span-full p-5 text-sm text-slate-500">No dashboard records yet.</div>}
        {loading && Array.from({ length: 8 }, (_, index) => <div key={index} className="enterprise-card h-[126px] animate-pulse bg-slate-50" />)}
      </div>

      {error && <div role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-4 text-sm text-rose-700">Unable to load live dashboard data: {error}</div>}

      {data && <>
        <section className="grid gap-4 xl:grid-cols-2">
          <ChartCard tourId="status-chart" title="Application status" note="Portfolio distribution by current decision state">
            <ResponsiveContainer width="100%" height="100%"><PieChart>
              <Pie data={data.statusDistribution} dataKey="value" nameKey="name" innerRadius={62} outerRadius={88} paddingAngle={3} stroke="none">
                {data.statusDistribution.map((item, index) => <Cell key={item.name} fill={chartColors[index % chartColors.length]} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart></ResponsiveContainer>
            <div className="-mt-2 flex flex-wrap justify-center gap-x-4 gap-y-2">{data.statusDistribution.map((item, index) => <span key={item.name} className="inline-flex items-center gap-1.5 text-[10px] capitalize text-slate-500"><i className="h-2 w-2 rounded-full" style={{ backgroundColor: chartColors[index % chartColors.length] }} />{item.name} <b className="text-slate-700">{item.value}</b></span>)}</div>
          </ChartCard>

          <ChartCard tourId="regional-chart" title="Regional pendency" note="Applications currently in process by region">
            <ResponsiveContainer width="100%" height="100%"><BarChart data={data.regionPendency} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="#eef2f7" />
              <XAxis dataKey="region" tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="value" name="Applications" fill="#2563eb" radius={[5, 5, 0, 0]} maxBarSize={38} />
            </BarChart></ResponsiveContainer>
          </ChartCard>

          <ChartCard tourId="monthly-chart" title="Monthly application trends" note="New submissions across recent months">
            <ResponsiveContainer width="100%" height="100%"><AreaChart data={data.monthlyTrend} margin={{ top: 10, right: 8, left: -20, bottom: 0 }}>
              <defs><linearGradient id="submissionFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#2563eb" stopOpacity={0.22} /><stop offset="95%" stopColor="#2563eb" stopOpacity={0.01} /></linearGradient></defs>
              <CartesianGrid vertical={false} stroke="#eef2f7" />
              <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fontSize: 9, fill: '#64748b' }} />
              <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area type="monotone" dataKey="applications" name="Submissions" stroke="#2563eb" strokeWidth={2.5} fill="url(#submissionFill)" />
            </AreaChart></ResponsiveContainer>
          </ChartCard>

          <ChartCard tourId="workflow-chart" title="Workflow stage distribution" note="Applications across the approval lifecycle">
            <ResponsiveContainer width="100%" height="100%"><BarChart layout="vertical" data={data.stageDistribution} margin={{ top: 0, right: 16, left: 18, bottom: 0 }}>
              <CartesianGrid horizontal={false} stroke="#eef2f7" />
              <XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis type="category" dataKey="name" width={104} tickLine={false} axisLine={false} tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={formatStage} />
              <Tooltip contentStyle={tooltipStyle} labelFormatter={(value) => formatStage(String(value))} />
              <Bar dataKey="value" name="Applications" fill="#102a56" radius={[0, 5, 5, 0]} maxBarSize={17} />
            </BarChart></ResponsiveContainer>
          </ChartCard>

          <section data-tour="compliance-chart" className="enterprise-card p-5">
            <div className="mb-4 flex items-start justify-between"><div><h2 className="text-sm font-bold text-slate-800">Compliance completion</h2><p className="mt-1 text-[11px] text-slate-500">Verified requirements by category</p></div><span className="rounded-md bg-emerald-50 p-2 text-emerald-700"><ShieldAlert size={16} /></span></div>
            <div className="space-y-5 pt-1">{data.complianceCompletion.map((item) => <div key={item.name}>
              <div className="mb-2 flex justify-between text-xs"><span className="font-medium text-slate-700">{item.name}</span><b className="text-slate-600">{item.percent}%</b></div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${Math.min(100, Math.max(0, item.percent))}%` }} /></div>
            </div>)}{data.complianceCompletion.length === 0 && <p className="text-xs text-slate-500">No compliance records yet.</p>}</div>
          </section>

          <section className="enterprise-card p-5">
            <div data-tour="priority-queue" className="mb-3 flex items-start justify-between gap-3">
              <div><h2 className="text-sm font-bold text-slate-800">Priority action queue</h2><p className="mt-1 text-[11px] text-slate-500">Overdue and upcoming work in your authorized records</p></div>
              <span className={`rounded-md px-2 py-1 text-[10px] font-semibold ${overdueCount ? 'bg-rose-50 text-rose-700' : dueSoonCount ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'}`}>{attentionLabel}</span>
            </div>
            <ul className="divide-y divide-slate-100">{attentionItems.slice(0, 6).map((item) => {
              const days = daysUntil(item.due_date);
              const overdue = days < 0;
              const dueLabel = overdue ? `${Math.abs(days)} ${Math.abs(days) === 1 ? 'day' : 'days'} overdue` : days === 0 ? 'Due today' : `Due in ${days} days`;
              return <li key={`${item.kind}-${item.id}`} className="flex items-center justify-between gap-3 py-3">
                <div className="flex min-w-0 items-center gap-3"><span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${overdue ? 'bg-rose-50 text-rose-600' : days <= 7 ? 'bg-amber-50 text-amber-700' : 'bg-blue-50 text-brand-blue'}`}>{overdue ? <AlertTriangle size={15} /> : <CalendarClock size={15} />}</span>
                  <div className="min-w-0"><p className="truncate text-xs font-semibold text-slate-800">{item.title}</p><p className="mt-0.5 text-[10px] text-slate-500">{item.kind} · {new Date(item.due_date).toLocaleDateString()}</p></div>
                </div>
                <div className="shrink-0 text-right"><p className={`text-[10px] font-semibold ${overdue ? 'text-rose-600' : days <= 7 ? 'text-amber-700' : 'text-slate-500'}`}>{dueLabel}</p><Link to={deadlineLink(item)} className="rounded-md px-1 py-1 text-[10px] font-semibold text-brand-blue hover:bg-blue-50">Review</Link></div>
              </li>;
            })}</ul>
            {attentionItems.length === 0 && <div className="flex h-[165px] flex-col items-center justify-center text-center"><CheckCircle2 size={26} className="text-emerald-500" /><p className="mt-2 text-xs font-semibold text-slate-700">You’re all caught up</p><p className="mt-1 text-[10px] text-slate-500">No overdue items or deadlines in the next 30 days.</p></div>}
          </section>
        </section>

        <section className="enterprise-card overflow-hidden">
          <div data-tour="recent-applications" className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
            <div><h2 className="text-sm font-bold text-slate-800">Recent applications</h2><p className="mt-1 text-[11px] text-slate-500">Latest records in your authorized portfolio</p></div>
            <div className="flex w-full flex-wrap gap-2 sm:w-auto">
              <input aria-label="Search recent applications" placeholder="Search ID, institution..." value={tableSearch} onChange={(event) => setTableSearch(event.target.value)} className="h-9 min-w-0 flex-1 px-3 text-xs sm:w-52" />
              <button onClick={() => void exportApplications()} disabled={exporting} className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600 transition hover:bg-slate-50 disabled:opacity-50">{exporting ? 'Exporting…' : 'Export CSV'}</button>
              <Link to="/applications" className="inline-flex h-9 items-center gap-1 rounded-lg bg-brand-navy px-3 text-xs font-semibold text-white transition hover:bg-blue-900">All applications <ArrowRight size={13} /></Link>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-[850px] w-full text-left text-xs">
              <thead className="bg-slate-50/80 text-[10px] uppercase tracking-wide text-slate-500"><tr>{['Application', 'Institution', 'Region', 'Current stage', 'Officer', 'Submitted', 'Pending', 'Status'].map((label) => <th key={label} className="px-4 py-3 font-semibold">{label}</th>)}</tr></thead>
              <tbody className="divide-y divide-slate-100">{visibleApplications.map((item) => <tr key={item.id} className="transition hover:bg-slate-50/70">
                <td className="px-4 py-3"><Link to={`/applications/${item.id}`} className="font-semibold text-brand-blue hover:underline">{item.id}</Link></td>
                <td className="px-4 py-3 font-medium text-slate-700">{item.institution}</td>
                <td className="px-4 py-3 text-slate-500">{item.region}</td>
                <td className="px-4 py-3 capitalize text-slate-600">{formatStage(item.stage)}</td>
                <td className="px-4 py-3 text-slate-600">{item.officer}</td>
                <td className="px-4 py-3 text-slate-500">{item.submittedAt ? new Date(item.submittedAt).toLocaleDateString() : '—'}</td>
                <td className="px-4 py-3 text-slate-600">{item.daysPending} days</td>
                <td className="px-4 py-3"><span className={`rounded-full px-2 py-1 text-[10px] font-semibold capitalize ${statusTone(item.status)}`}>{item.status}</span></td>
              </tr>)}</tbody>
            </table>
            {visibleApplications.length === 0 && <div className="p-8 text-center text-xs text-slate-500">{applications.length ? 'No recent applications match your search.' : 'No applications available in this view.'}</div>}
          </div>
          <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3 text-[10px] text-slate-500"><span>Showing {visibleApplications.length} recent records</span><Link to="/applications" className="font-semibold text-brand-blue hover:underline">Open application workspace</Link></div>
        </section>
      </>}
      {tourStep !== null && <DashboardTour step={tourStep} onStepChange={changeTourStep} onClose={closeTour} />}
    </div>
  );
}
