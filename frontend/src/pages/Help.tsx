import { AlertTriangle, ArrowRight, BookOpen, CheckCircle2, ClipboardList, Landmark, ShieldCheck, Users } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

const scenarios: { title: string; path: string; to: string; action: string; roles?: string[] }[] = [
  { title: '1 · Normal application', path: 'Create a record as an institution, follow its timeline, then advance it through configured stages.', to: '/applications', action: 'Explore applications' },
  { title: '2 · Deficiency and resubmission', path: 'Officers can inspect returned demo cases; institutions can respond to returned cases in their own account scope.', to: '/applications', action: 'Open permitted applications' },
  { title: '3 · EVC visit', path: 'Schedule a visit, then record findings and a recommendation as the committee.', to: '/evc', action: 'Open EVC schedule', roles: ['admin', 'regional_officer', 'bureau_officer', 'evc_committee'] },
  { title: '4 · Upcoming compliance', path: 'Review due dates, attach evidence, and verify or request a correction.', to: '/compliance', action: 'Open compliance', roles: ['admin', 'regional_officer', 'bureau_officer', 'institution'] },
  { title: '5 · Expired lease', path: 'Review an expiry record and follow the replacement document through review.', to: '/lease', action: 'Open lease tracking', roles: ['admin', 'regional_officer', 'bureau_officer', 'institution'] },
  { title: '6 · Overdue escalation', path: 'Run the deadline monitor and inspect generated alerts and audit history.', to: '/notifications', action: 'View notifications', roles: ['admin', 'bureau_officer'] },
];
export default function Help() {
  const { user } = useAuth();
  const visibleScenarios = scenarios.filter((scenario) => !scenario.roles || scenario.roles.includes(user?.role || ''));
  return <div className="space-y-6">
    <header><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Workspace resources</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">Help &amp; system information</h1><p className="mt-1 text-sm text-slate-500">Understand roles, demo safeguards and the end-to-end workflows.</p></header>
    <section className="enterprise-card border-blue-100 bg-blue-50/60 p-5">
      <div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-100 text-brand-blue"><BookOpen size={18} /></span><div><h2 className="text-sm font-bold text-slate-800">New here? Quick guide</h2><p className="mt-0.5 text-[10px] text-slate-500">A quick explanation of the main workspace sections.</p></div></div>
      <div className="mt-4 grid gap-x-6 gap-y-3 text-xs sm:grid-cols-2 lg:grid-cols-3">
        <p><b className="text-slate-800">Dashboard:</b> <span className="text-slate-600">Portfolio overview, deadlines and charts.</span></p>
        <p><b className="text-slate-800">Applications:</b> <span className="text-slate-600">Create, find and follow application workflows.</span></p>
        <p><b className="text-slate-800">Documents:</b> <span className="text-slate-600">Upload evidence and review document status.</span></p>
        <p><b className="text-slate-800">Compliance &amp; Lease:</b> <span className="text-slate-600">Track undertakings, evidence and lease dates.</span></p>
        <p><b className="text-slate-800">EVC scheduling:</b> <span className="text-slate-600">Coordinate visits and record committee findings.</span></p>
        <p><b className="text-slate-800">AICTE public data:</b> <span className="text-slate-600">View public institution data when a verified source is connected.</span></p>
        <p><b className="text-slate-800">Reports &amp; Notifications:</b> <span className="text-slate-600">Review summaries and updates for your account.</span></p>
        <p><b className="text-slate-800">Admin tools:</b> <span className="text-slate-600">Manage users and example workflow settings (admin only).</span></p>
      </div>
      <p className="mt-4 border-t border-blue-100 pt-3 text-[10px] text-slate-600">First time? Start at Dashboard, then open an application to explore its documents, workflow and related records. Your available actions depend on your account role.</p>
    </section>
    <section className="enterprise-card p-5">
      <div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-brand-blue"><Users size={18} /></span><div><h2 className="text-sm font-bold text-slate-800">Workspace roles</h2><p className="mt-0.5 text-[10px] text-slate-500">Access and capabilities depend on the assigned account role.</p></div></div>
      <ul className="mt-4 grid gap-3 sm:grid-cols-2">
        {[
          ['Administrator', 'Manages users and configurable demo settings.'],
          ['Regional officer', 'Reviews applications and records within assigned region.'],
          ['Bureau officer', 'Reviews workflow, reports and audit records.'],
          ['EVC / Committee', 'Records EVC visit findings and recommendations.'],
          ['Institution', 'Submits applications, documents and compliance evidence.'],
        ].map(([role, description]) => <li key={role} className="flex gap-3 rounded-xl border border-slate-100 bg-slate-50/60 p-3"><span className="mt-0.5 text-brand-blue"><CheckCircle2 size={15} /></span><div><b className="text-xs text-slate-800">{role}</b><p className="mt-1 text-[10px] leading-4 text-slate-500">{description}</p></div></li>)}
      </ul>
    </section>
    <section className="rounded-xl border border-amber-200 bg-amber-50 p-5">
      <div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-100 text-amber-800"><ShieldCheck size={18} /></span><div><h2 className="text-sm font-bold text-amber-950">Important safeguards</h2><p className="mt-0.5 text-[10px] text-amber-900">Please note these limitations before using demo records.</p></div></div>
      <ul className="mt-4 space-y-2 text-xs leading-5 text-amber-950">{[
        'This is a fictional demo and is not officially integrated with AICTE or any official system.',
        'Workflow rules, deadlines, escalation levels and reminder windows are configurable examples, not regulatory assumptions.',
        'Automated indicators are not statutory approvals or final decisions. Only competent authorized officials may record official findings and approvals.',
        'OCR/text extraction is advisory and never determines fraud or document authenticity.',
      ].map((item) => <li key={item} className="flex gap-2"><AlertTriangle size={14} className="mt-0.5 shrink-0" />{item}</li>)}</ul>
    </section>
    <section id="demo" className="enterprise-card p-5">
      <div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50 text-violet-700"><BookOpen size={18} /></span><div><h2 className="text-sm font-bold text-slate-800">Demo workflow scenarios</h2><p className="mt-0.5 text-[10px] text-slate-500">Follow these guided paths to explore end-to-end product interactions.</p></div></div>
      <div className="mt-4 grid gap-3 lg:grid-cols-2">{visibleScenarios.map(({ title, path, to, action }) => <article key={title} className="flex gap-3 rounded-xl border border-slate-100 p-4 transition hover:border-blue-100 hover:bg-slate-50/50"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-brand-blue"><ClipboardList size={16} /></span><div className="min-w-0 flex-1"><b className="text-xs text-slate-800">{title}</b><p className="mt-1 text-[10px] leading-5 text-slate-500">{path}</p><Link to={to} className="mt-2 inline-flex items-center gap-1 text-[10px] font-semibold text-brand-blue hover:underline">{action}<ArrowRight size={12} /></Link></div></article>)}</div>
      <p className="mt-4 flex items-center gap-2 rounded-lg bg-slate-50 p-3 text-[10px] text-slate-600"><Landmark size={14} className="shrink-0 text-slate-400" />Reset seeded data from Administrator → User Management → Reset demo data.</p>
    </section>
  </div>;
}
