import { BarChart3, Bell, Building2, CalendarDays, CheckCircle2, FileText, Filter, ShieldCheck, TrendingUp } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const API_BASE = 'http://localhost:8000/api';

type Kpi = {
  label: string;
  value: number;
  change: string;
};

type AppRecord = {
  id: string;
  institution: string;
  region: string;
  type: string;
  submittedAt: string;
  stage: string;
  officer: string;
  daysPending: number;
  deadline: string;
  status: string;
  priority: string;
};

type ComplianceRecord = {
  institution: string;
  applicationId: string;
  description: string;
  dueDate: string;
  status: string;
  daysRemaining: number;
  officer: string;
};

export default function App() {
  const [kpis, setKpis] = useState<Kpi[]>([]);
  const [statusDistribution, setStatusDistribution] = useState<any[]>([]);
  const [regionPendency, setRegionPendency] = useState<any[]>([]);
  const [monthlyTrend, setMonthlyTrend] = useState<any[]>([]);
  const [complianceCompletion, setComplianceCompletion] = useState<any[]>([]);
  const [applications, setApplications] = useState<AppRecord[]>([]);
  const [compliance, setCompliance] = useState<ComplianceRecord[]>([]);
  const [selectedRole, setSelectedRole] = useState('Administrator');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dashboardRes, appsRes, complianceRes] = await Promise.all([
          fetch(`${API_BASE}/dashboard`),
          fetch(`${API_BASE}/applications`),
          fetch(`${API_BASE}/compliance`),
        ]);

        if (!dashboardRes.ok || !appsRes.ok || !complianceRes.ok) {
          throw new Error('Failed to load data');
        }

        const dashboard = await dashboardRes.json();
        const appData = await appsRes.json();
        const complianceData = await complianceRes.json();

        setKpis(dashboard.kpis ?? []);
        setStatusDistribution(dashboard.statusDistribution ?? []);
        setRegionPendency(dashboard.regionPendency ?? []);
        setMonthlyTrend(dashboard.monthlyTrend ?? []);
        setComplianceCompletion(dashboard.complianceCompletion ?? []);
        setApplications(appData ?? []);
        setCompliance(complianceData ?? []);
      } catch (error) {
        console.error('Failed to fetch dashboard data', error);
      }
    };

    fetchData();
  }, []);

  const filteredApps = useMemo(() => applications, [applications]);

  return (
    <div className="w-full min-h-screen bg-slate-100 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-slate-950/95 text-white shadow-lg backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-blue-300">AICTE Approval Intelligence</div>
            <h1 className="text-2xl font-bold">NEXORA AICTE</h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm">
              <span className="text-slate-400">Role:</span> {selectedRole}
            </div>
            <div className="rounded-full bg-white/10 p-2"><Bell className="h-4 w-4" /></div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <section className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-blue-700">Dashboard overview</p>
            <h2 className="mt-2 text-3xl font-bold text-slate-900">Approval Workflow & Compliance Management</h2>
          </div>
          <div className="flex flex-wrap gap-3">
            {['Administrator', 'Regional Officer', 'Bureau Officer', 'EVC / Committee', 'Institution'].map((role) => (
              <button
                key={role}
                type="button"
                onClick={() => setSelectedRole(role)}
                className={`rounded-full px-4 py-2 text-sm font-medium transition ${selectedRole === role ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50'}`}
              >
                {role}
              </button>
            ))}
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {kpis.map((kpi) => (
            <div key={kpi.label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
              <div className="flex items-center justify-between text-sm text-slate-500">
                <span>{kpi.label}</span>
                <div className="rounded-full bg-blue-50 p-2 text-blue-600"><TrendingUp className="h-4 w-4" /></div>
              </div>
              <div className="mt-5 flex items-end justify-between">
                <span className="text-3xl font-bold text-slate-900">{kpi.value}</span>
                <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-700">{kpi.change}</span>
              </div>
            </div>
          ))}
        </section>

        <section className="mt-8 grid gap-6 xl:grid-cols-[1.6fr_1fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Insights</p>
                <h3 className="text-xl font-bold text-slate-900">Application status distribution</h3>
              </div>
              <button className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600"><Filter className="h-4 w-4" /> Filters</button>
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={statusDistribution}>
                  <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                    {statusDistribution.map((entry, index) => (
                      <Cell key={`cell-${entry.name}`} fill={['#2563eb', '#38bdf8', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'][index % 6]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Coverage</p>
            <h3 className="mt-2 text-xl font-bold text-slate-900">Regional pendency</h3>
            <div className="mt-6 h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={regionPendency} dataKey="value" nameKey="region" innerRadius={55} outerRadius={90} paddingAngle={2}>
                    {regionPendency.map((entry, index) => (
                      <Cell key={entry.region} fill={['#2563eb', '#0ea5e9', '#10b981', '#f59e0b', '#64748b'][index % 5]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 space-y-2">
              {regionPendency.map((region) => (
                <div key={region.region} className="flex items-center justify-between text-sm text-slate-700">
                  <span>{region.region}</span>
                  <span className="font-semibold">{region.value}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <h3 className="text-xl font-bold text-slate-900">Monthly application processing trend</h3>
            <div className="mt-6 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyTrend}>
                  <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="applications" radius={[8, 8, 0, 0]} fill="#2563eb" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <h3 className="text-xl font-bold text-slate-900">Compliance completion</h3>
            <div className="mt-6 space-y-5">
              {complianceCompletion.map((item) => (
                <div key={item.name}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-700">{item.name}</span>
                    <span className="font-semibold text-slate-900">{item.percent}%</span>
                  </div>
                  <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-200">
                    <div className="h-full rounded-full bg-gradient-to-r from-blue-500 to-emerald-500" style={{ width: `${item.percent}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="mb-5 flex items-center justify-between gap-3">
            <div>
              <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Workflow</p>
              <h3 className="text-xl font-bold text-slate-900">Application management</h3>
            </div>
            <button className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white"><FileText className="h-4 w-4" /> Create new application</button>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-semibold">Application ID</th>
                  <th className="px-4 py-3 font-semibold">Institution</th>
                  <th className="px-4 py-3 font-semibold">Region</th>
                  <th className="px-4 py-3 font-semibold">Type</th>
                  <th className="px-4 py-3 font-semibold">Current Stage</th>
                  <th className="px-4 py-3 font-semibold">Officer</th>
                  <th className="px-4 py-3 font-semibold">Deadline</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {filteredApps.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-900">{item.id}</td>
                    <td className="px-4 py-3">{item.institution}</td>
                    <td className="px-4 py-3">{item.region}</td>
                    <td className="px-4 py-3">{item.type}</td>
                    <td className="px-4 py-3">{item.stage}</td>
                    <td className="px-4 py-3">{item.officer}</td>
                    <td className="px-4 py-3">{item.deadline}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${item.status.includes('Deficiency') ? 'bg-amber-100 text-amber-700' : item.status.includes('Awaiting') ? 'bg-blue-100 text-blue-700' : 'bg-emerald-100 text-emerald-700'}`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-blue-600" />
              <h3 className="text-xl font-bold text-slate-900">Compliance & undertaking tracker</h3>
            </div>
            <div className="mt-6 space-y-4">
              {compliance.map((item) => (
                <div key={`${item.applicationId}-${item.description}`} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-900">{item.institution}</p>
                      <p className="text-sm text-slate-600">{item.applicationId} • {item.description}</p>
                    </div>
                    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${item.status === 'Overdue' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>
                      {item.status}
                    </span>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-sm text-slate-600">
                    <span>Due: {item.dueDate}</span>
                    <span>{item.daysRemaining} days</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <div className="flex items-center gap-2">
              <CalendarDays className="h-5 w-5 text-emerald-600" />
              <h3 className="text-xl font-bold text-slate-900">Upcoming EVC & deadlines</h3>
            </div>
            <div className="mt-6 space-y-4">
              {[
                { title: 'EVC inspection - Apex Engineering', date: '2024-10-15', type: 'Priority' },
                { title: 'Compliance reminder - Global Heights', date: '2024-10-17', type: 'Due Soon' },
                { title: 'Committee review - Blue Horizon', date: '2024-10-22', type: 'Review' },
              ].map((item) => (
                <div key={item.title} className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div>
                    <p className="font-semibold text-slate-900">{item.title}</p>
                    <p className="text-sm text-slate-600">{item.date}</p>
                  </div>
                  <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-700">{item.type}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <div className="flex items-center gap-2 text-green-600"><CheckCircle2 className="h-5 w-5" /><span className="text-base font-semibold">Workflow automation</span></div>
            <p className="mt-4 text-sm text-slate-600">Configurable stages, automatic progression, mandatory reasons for returns, and immutable transition logs.</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <div className="flex items-center gap-2 text-blue-600"><Building2 className="h-5 w-5" /><span className="text-base font-semibold">Document verification</span></div>
            <p className="mt-4 text-sm text-slate-600">Upload, validate, OCR-assisted review, document expiry monitoring, and renewal compliance checks.</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <div className="flex items-center gap-2 text-violet-600"><BarChart3 className="h-5 w-5" /><span className="text-base font-semibold">Executive reporting</span></div>
            <p className="mt-4 text-sm text-slate-600">Role-based dashboards, regional analytics, ageing trends, and escalation-ready management reports.</p>
          </div>
        </section>
      </main>
    </div>
  );
}
