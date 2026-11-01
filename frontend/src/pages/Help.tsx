import { AlertTriangle, BookOpen, CheckCircle2, ClipboardList, Landmark, ShieldCheck, Users } from 'lucide-react';

const scenarios = [
  ['1 · Normal application', 'Applications → New application → submit → Applications → open record → officer advances configured stages.'],
  ['2 · Deficiency and resubmission', 'Open APP-2026-0002 → officer returns with a reason → institution opens the record and selects Resubmit.'],
  ['3 · EVC visit', 'EVC Scheduling → schedule APP-2026-0003 → committee records findings and recommendation → inspect application stage.'],
  ['4 · Upcoming compliance', 'Compliance Management → create undertaking due soon or review seeded record → institution submits evidence → officer verifies.'],
  ['5 · Expired lease', 'Lease & Expiry → view expired lease → institution uploads renewal → replacement enters verification.'],
  ['6 · Overdue escalation', 'Administrator → User Management → Run deadline monitor → Notifications / Applications → inspect the overdue escalation.'],
];
export default function Help() {
  return <div className="space-y-6">
    <header><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Workspace resources</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">Help &amp; system information</h1><p className="mt-1 text-sm text-slate-500">Understand roles, demo safeguards and the end-to-end workflows.</p></header>
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
    <section className="enterprise-card p-5">
      <div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50 text-violet-700"><BookOpen size={18} /></span><div><h2 className="text-sm font-bold text-slate-800">Demo workflow scenarios</h2><p className="mt-0.5 text-[10px] text-slate-500">Follow these guided paths to explore end-to-end product interactions.</p></div></div>
      <div className="mt-4 grid gap-3 lg:grid-cols-2">{scenarios.map(([title, path]) => <article key={title} className="flex gap-3 rounded-xl border border-slate-100 p-4 transition hover:border-blue-100 hover:bg-slate-50/50"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-brand-blue"><ClipboardList size={16} /></span><div><b className="text-xs text-slate-800">{title}</b><p className="mt-1 text-[10px] leading-5 text-slate-500">{path}</p></div></article>)}</div>
      <p className="mt-4 flex items-center gap-2 rounded-lg bg-slate-50 p-3 text-[10px] text-slate-600"><Landmark size={14} className="shrink-0 text-slate-400" />Reset seeded data from Administrator → User Management → Reset demo data.</p>
    </section>
  </div>;
}
