import {
  ArrowRight, BadgeCheck, BookOpen, Building2, CalendarClock, ChartNoAxesCombined,
  ClipboardCheck, FileCheck2, Globe2, Landmark, LockKeyhole, ShieldCheck, Users,
  Workflow,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

const features = [
  {
    icon: ClipboardCheck,
    title: 'Applications & workflow',
    description: 'Submit and resubmit applications, review case history, record scrutiny notes and track each case through configurable stages.',
  },
  {
    icon: FileCheck2,
    title: 'Documents & evidence',
    description: 'Upload supporting files, check verification and expiry status, and keep evidence connected to its application.',
  },
  {
    icon: ShieldCheck,
    title: 'Compliance & leases',
    description: 'Track undertakings, evidence, verification, due dates and lease renewals from a shared workspace.',
  },
  {
    icon: CalendarClock,
    title: 'EVC visit coordination',
    description: 'Schedule evaluation visits, assign committee members and record findings and recommendations.',
  },
  {
    icon: ChartNoAxesCombined,
    title: 'Dashboards & reports',
    description: 'Review role-scoped application, regional, deadline, compliance and document summaries; export application lists.',
  },
  {
    icon: Users,
    title: 'Roles, alerts & audit trail',
    description: 'Give each team member a role-appropriate workspace, receive notifications and trace important workflow actions.',
  },
  {
    icon: Globe2,
    title: 'Public institution data',
    description: 'A separate view for public institution information when a verified data source is configured; it stays separate from demo applications.',
  },
  {
    icon: BookOpen,
    title: 'Help & workspace guide',
    description: 'Explore role-specific guidance and demo scenarios. The assistant can explain the workspace but cannot access records or make decisions.',
  },
];

const workflow = ['Submit', 'Scrutiny', 'Deficiency', 'EVC visit', 'EVC review', 'Committee', 'Decision', 'Final status'];

const roles = [
  ['Institution', 'Submit applications, upload documents and compliance evidence, and follow owned records.'],
  ['Regional Officer', 'Review region-scoped applications, record scrutiny and coordinate EVC visits.'],
  ['Bureau Officer', 'Coordinate workflow review, decisions, reports and audit history.'],
  ['EVC / Committee', 'View assigned EVC-stage work and record visit findings and recommendations.'],
  ['Administrator', 'Manage accounts and configure example workflow and reminder settings.'],
];

export default function Landing() {
  const { user } = useAuth();
  const accessHref = user ? '/dashboard' : '/login';

  return (
    <main className="min-h-screen overflow-hidden bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="relative z-10 border-b border-slate-200/80 bg-white/90 dark:border-slate-800 dark:bg-slate-950/90">
        <nav aria-label="Main navigation" className="mx-auto flex h-[76px] max-w-7xl items-center justify-between px-5 sm:px-8">
          <Link to="/" className="flex items-center gap-3" aria-label="NEXORA AICTE home">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-navy text-white"><Landmark size={21} /></span>
            <span>
              <span className="block text-sm font-bold tracking-tight text-brand-navy dark:text-white">NEXORA <span className="font-medium">AICTE</span></span>
              <span className="block text-[10px] text-slate-500 dark:text-slate-400">Approval &amp; Compliance Intelligence</span>
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <a href="#platform" className="hidden px-3 py-2 text-sm font-medium text-slate-600 transition hover:text-brand-blue dark:text-slate-300 sm:inline-flex">What it does</a>
            <a href="#workflow" className="hidden px-3 py-2 text-sm font-medium text-slate-600 transition hover:text-brand-blue dark:text-slate-300 md:inline-flex">Workflow</a>
            <a href="#roles" className="hidden px-3 py-2 text-sm font-medium text-slate-600 transition hover:text-brand-blue dark:text-slate-300 lg:inline-flex">Who it serves</a>
            <Link to={accessHref} className="inline-flex h-10 items-center gap-2 rounded-lg bg-brand-blue px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700">
              {user ? 'Open workspace' : 'Sign in'} <ArrowRight size={15} />
            </Link>
          </div>
        </nav>
      </header>

      <section className="relative isolate">
        <div className="absolute inset-0 -z-10 bg-gradient-to-br from-blue-50 via-white to-sky-50 dark:from-slate-900 dark:via-slate-950 dark:to-slate-900" />
        <div className="absolute -right-36 top-8 -z-10 h-96 w-96 rounded-full bg-blue-200/30 blur-3xl dark:bg-blue-900/20" />
        <div className="mx-auto grid max-w-7xl items-center gap-14 px-5 py-16 sm:px-8 sm:py-20 lg:grid-cols-[1.05fr_.95fr] lg:gap-10 lg:py-24">
          <div className="max-w-2xl">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-white/80 px-3.5 py-2 text-xs font-semibold text-brand-blue shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:text-blue-300">
              <BadgeCheck size={15} /> One workspace for every stage
            </div>
            <h1 className="page-title text-4xl font-bold leading-[1.12] tracking-tight text-brand-navy dark:text-white sm:text-5xl lg:text-[60px]">
              Approvals made
              <span className="block text-brand-blue">clear and connected.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-slate-600 dark:text-slate-300 sm:text-lg">
              A simpler way for institutional teams and reviewers to manage applications, documents and compliance—all in one place.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link to={accessHref} className="inline-flex h-12 items-center gap-2 rounded-lg bg-brand-blue px-5 text-sm font-semibold text-white shadow-lg shadow-blue-900/15 transition hover:bg-blue-700">
                {user ? 'Go to your workspace' : 'Sign in to your workspace'} <ArrowRight size={16} />
              </Link>
              {!user && <Link to="/register" className="inline-flex h-12 items-center rounded-lg border border-slate-300 bg-white px-5 text-sm font-semibold text-slate-700 transition hover:border-blue-300 hover:text-brand-blue dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">Request institution access</Link>}
            </div>
            <div className="mt-8 flex flex-wrap gap-x-6 gap-y-3 text-xs font-medium text-slate-500 dark:text-slate-400">
              <span className="inline-flex items-center gap-2"><LockKeyhole size={14} className="text-emerald-600 dark:text-emerald-400" /> Secure sign-in</span>
              <span className="inline-flex items-center gap-2"><Workflow size={15} className="text-emerald-600 dark:text-emerald-400" /> Clear review stages</span>
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-[530px]">
            <div className="absolute -inset-5 rounded-[30px] bg-blue-200/35 blur-2xl dark:bg-blue-950/40" />
            <div className="relative rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_24px_80px_-28px_rgba(15,42,86,.32)] dark:border-slate-700 dark:bg-slate-900 sm:p-7">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[.12em] text-slate-400">Workspace overview</p>
                  <h2 className="mt-1 text-lg font-bold text-brand-navy dark:text-white">Application journey</h2>
                </div>
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-brand-blue dark:bg-blue-950/60 dark:text-blue-300"><Building2 size={19} /></span>
              </div>
              <div className="mt-7 rounded-xl border border-slate-100 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/70">
                <div className="flex items-center justify-between gap-3">
                  <div><p className="text-sm font-semibold text-slate-800 dark:text-slate-100">Institution application</p><p className="mt-1 text-xs text-slate-500">A clear view from start to decision</p></div>
                  <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">IN REVIEW</span>
                </div>
                <div className="mt-7 grid grid-cols-4 gap-y-4 sm:grid-cols-8">
                  {workflow.map((step, index) => (
                    <div key={step} className="relative">
                      {index < workflow.length - 1 && <span className={`absolute left-7 right-0 top-3.5 hidden h-px sm:block ${index < 2 ? 'bg-blue-300 dark:bg-blue-700' : 'bg-slate-200 dark:bg-slate-700'}`} />}
                      <span className={`relative flex h-7 w-7 items-center justify-center rounded-full border-2 ${index < 2 ? 'border-brand-blue bg-brand-blue text-white' : 'border-slate-200 bg-white text-slate-400 dark:border-slate-700 dark:bg-slate-900'}`}>
                        {index < 2 ? <BadgeCheck size={15} /> : <span className="text-[10px] font-semibold">{index + 1}</span>}
                      </span>
                      <span className="mt-2 block max-w-12 text-[9px] font-medium leading-3 text-slate-500 dark:text-slate-400 sm:text-[8px]">{step}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-slate-100 p-4 dark:border-slate-800">
                  <p className="text-xs text-slate-500 dark:text-slate-400">Documents</p>
                  <p className="mt-1 text-lg font-bold text-brand-navy dark:text-white">Organised</p>
                </div>
                <div className="rounded-xl border border-slate-100 p-4 dark:border-slate-800">
                  <p className="text-xs text-slate-500 dark:text-slate-400">Next step</p>
                  <p className="mt-1 text-lg font-bold text-brand-navy dark:text-white">Review</p>
                </div>
              </div>
              <p className="mt-5 flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400"><ShieldCheck size={14} className="text-emerald-600 dark:text-emerald-400" /> Role-based access with an auditable workflow</p>
            </div>
          </div>
        </div>
      </section>

      <section id="platform" className="scroll-mt-8 border-t border-slate-100 bg-white py-16 dark:border-slate-800 dark:bg-slate-950 sm:py-20">
        <div className="mx-auto max-w-7xl px-5 sm:px-8">
          <div className="max-w-2xl">
            <p className="text-xs font-bold uppercase tracking-[.14em] text-brand-blue">What the program does</p>
            <h2 className="page-title mt-3 text-3xl font-bold tracking-tight text-brand-navy dark:text-white sm:text-4xl">One place to manage the approval journey.</h2>
            <p className="mt-4 text-sm leading-6 text-slate-600 dark:text-slate-300">NEXORA brings application review, institution evidence, compliance follow-up and operational reporting into one role-based workspace.</p>
          </div>
          <div className="mt-9 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, description }) => (
              <article key={title} className="rounded-2xl border border-slate-200 bg-white p-6 transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-lg hover:shadow-slate-900/5 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-brand-blue dark:bg-blue-950/60 dark:text-blue-300"><Icon size={20} /></span>
                <h3 className="mt-5 text-base font-bold text-brand-navy dark:text-white">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="workflow" className="scroll-mt-8 border-t border-slate-100 bg-slate-50 py-16 dark:border-slate-800 dark:bg-slate-900/50 sm:py-20">
        <div className="mx-auto grid max-w-7xl gap-10 px-5 sm:px-8 lg:grid-cols-[.8fr_1.2fr] lg:items-start">
          <div>
            <p className="text-xs font-bold uppercase tracking-[.14em] text-brand-blue">How it works</p>
            <h2 className="page-title mt-3 text-3xl font-bold tracking-tight text-brand-navy dark:text-white">A traceable path from submission to status.</h2>
            <p className="mt-4 text-sm leading-6 text-slate-600 dark:text-slate-300">Each configured transition updates the application timeline and can notify the relevant team. Returned applications can be corrected and resubmitted by the institution.</p>
            <p className="mt-4 text-xs leading-5 text-slate-500 dark:text-slate-400">Stages, deadlines and reminders shown here are prototype examples—not official regulatory rules or timelines.</p>
          </div>
          <ol className="grid gap-3 sm:grid-cols-2">
            {[
              ['01', 'Application submission', 'Institution submits application details and supporting evidence.'],
              ['02', 'Initial scrutiny', 'An authorized reviewer checks the submission and records observations.'],
              ['03', 'Deficiency check', 'Missing information can be requested, corrected and resubmitted.'],
              ['04', 'EVC scheduling', 'A visit can be coordinated and committee members assigned.'],
              ['05', 'EVC completion', 'The committee records visit findings and recommendations.'],
              ['06', 'Committee stage', 'The case moves through its configured committee review.'],
              ['07', 'Authorised decision', 'An authorized role records the next decision in the workflow.'],
              ['08', 'Final application status', 'The application timeline and status show the recorded outcome.'],
            ].map(([number, title, description]) => (
              <li key={number} className="flex gap-4 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-xs font-bold text-brand-blue dark:bg-blue-950/60 dark:text-blue-300">{number}</span>
                <div><h3 className="text-sm font-bold text-brand-navy dark:text-white">{title}</h3><p className="mt-1 text-xs leading-5 text-slate-600 dark:text-slate-300">{description}</p></div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section id="roles" className="scroll-mt-8 border-t border-slate-100 bg-white py-16 dark:border-slate-800 dark:bg-slate-950 sm:py-20">
        <div className="mx-auto max-w-7xl px-5 sm:px-8">
          <div className="grid gap-8 lg:grid-cols-[.7fr_1.3fr]">
            <div>
              <p className="text-xs font-bold uppercase tracking-[.14em] text-brand-blue">Built for different teams</p>
              <h2 className="page-title mt-3 text-3xl font-bold tracking-tight text-brand-navy dark:text-white">The right view for each role.</h2>
              <p className="mt-4 text-sm leading-6 text-slate-600 dark:text-slate-300">Accounts see role-appropriate pages and records. Institutions are limited to records linked to their account; officers work within their assigned permissions.</p>
            </div>
            <ul className="grid gap-3 sm:grid-cols-2">
              {roles.map(([role, description]) => (
                <li key={role} className="rounded-xl border border-slate-200 p-4 dark:border-slate-800">
                  <h3 className="text-sm font-bold text-brand-navy dark:text-white">{role}</h3>
                  <p className="mt-1.5 text-xs leading-5 text-slate-600 dark:text-slate-300">{description}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-6 text-xs text-slate-500 dark:text-slate-400 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <span>© {new Date().getFullYear()} NEXORA AICTE · Demo workflow, not an official AICTE product</span>
          <Link to={accessHref} className="inline-flex items-center gap-1 font-semibold text-brand-blue hover:underline">{user ? 'Open workspace' : 'Sign in'} <ArrowRight size={13} /></Link>
        </div>
      </footer>
    </main>
  );
}
