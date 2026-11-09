import { AlertTriangle, BellRing, FileText, GitBranch, Save, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { apiDelete, apiGet, apiPost, apiPut } from '../api/client';

type Rule = { stage_key: string; stage_name: string; stage_order: number; requires_scrutiny: boolean; requires_evc: boolean; requires_committee: boolean; deadline_days: number | null; allowed_roles: string; is_active: boolean };
type AphRule = { key: string; label: string; rule_category: string; clauses: string[]; mandatory_steps: string[]; conditional_steps: string[]; required_documents: string[]; processing_timeline: string; source_document: string; process_notes: string[]; ter_charges: string; scope_notes: string[] };
type Config = { values: number[] };
export default function WorkflowConfig() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [aphRules, setAphRules] = useState<AphRule[]>([]);
  const [intervals, setIntervals] = useState<number[]>([]);
  const [escalation, setEscalation] = useState('{"levels":[1,2,3],"intervals":[7,14,30],"targets":{}}');
  const [category, setCategory] = useState('');
  const [categories, setCategories] = useState<{ id: number; name: string }[]>([]);
  const [error, setError] = useState('');
  async function load() {
    try {
      const [r, reminder, cats, aph] = await Promise.all([
        apiGet<Rule[]>('/workflow/rules'), apiGet<{ intervals: number[] }>('/admin/reminder-intervals'),
        apiGet<{ id: number; name: string }[]>('/admin/document-categories'),
        apiGet<AphRule[]>('/workflow/aph-rules'),
      ]);
      setRules(r); setIntervals(reminder.intervals); setCategories(cats); setAphRules(aph);
      const config = await apiGet<Record<string, unknown>>('/admin/escalation-config');
      setEscalation(JSON.stringify(config, null, 2));
    } catch (err) { setError(err instanceof Error ? err.message : 'Unable to load configuration'); }
  }
  useEffect(() => { void load(); }, []);
  async function saveRule(rule: Rule) {
    try { await apiPut(`/workflow/rules/${rule.stage_key}`, rule); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Rule save failed'); }
  }
  async function saveIntervals() {
    try { await apiPut('/admin/reminder-intervals', intervals); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Reminder save failed'); }
  }
  async function saveEscalation() {
    try { await apiPut('/admin/escalation-config', JSON.parse(escalation)); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Escalation config must be valid JSON'); }
  }
  async function addCategory(event: React.FormEvent) {
    event.preventDefault();
    try { await apiPost('/admin/document-categories', { name: category }); setCategory(''); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not add category'); }
  }
  return <div className="space-y-6">
    <header><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Administration · Example rules</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">Workflow configuration</h1><p className="mt-1 text-sm text-slate-500">Manage example workflow stages, reminders and document categories.</p></header>
    <p className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs leading-5 text-amber-950"><AlertTriangle size={16} className="mt-0.5 shrink-0 text-amber-700" />APH category routing and clause references below are based on the 2024-2027 handbook. Legacy stage-day values, reminder windows and escalation settings are prototype controls; APH processing windows do not use those day values.</p>
    {error && <p role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
    <section className="enterprise-card overflow-hidden">
      <div className="flex items-center gap-3 border-b border-slate-100 px-5 py-4"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-brand-blue"><GitBranch size={18} /></span><div><h2 className="text-sm font-bold text-slate-800">Workflow stages</h2><p className="mt-0.5 text-[10px] text-slate-500">Configure requirements and deadlines for each stage.</p></div></div>
      <div className="divide-y divide-slate-100">{rules.map((rule) => <article key={rule.stage_key} className="grid gap-4 p-4 md:grid-cols-[minmax(160px,1fr)_repeat(3,auto)_auto] md:items-center">
        <div><b className="text-xs text-slate-800">{rule.stage_order}. {rule.stage_name}</b><p className="mt-1 text-[10px] text-slate-500">{rule.stage_key} · roles: {rule.allowed_roles}</p></div>
        {(['requires_scrutiny', 'requires_evc', 'requires_committee'] as const).map((field) => <label key={field} className="flex items-center gap-2 text-[10px] capitalize text-slate-600"><input type="checkbox" checked={rule[field]} onChange={(e) => setRules(rules.map((item) => item.stage_key === rule.stage_key ? { ...item, [field]: e.target.checked } : item))} className="h-4 w-4 accent-blue-600" />{field.replace('requires_', '')}</label>)}
        <div className="flex items-center gap-2"><label className="text-[10px] text-slate-500">Legacy demo days<input aria-label="Legacy demo deadline days" type="number" min="0" value={rule.deadline_days ?? ''} onChange={(e) => setRules(rules.map((item) => item.stage_key === rule.stage_key ? { ...item, deadline_days: e.target.value ? Number(e.target.value) : null } : item))} className="mt-1 block h-9 w-24 px-2 text-xs" /></label><button onClick={() => saveRule(rule)} className="mt-4 inline-flex h-9 items-center gap-1.5 rounded-lg bg-brand-navy px-3 text-[10px] font-semibold text-white transition hover:bg-blue-900"><Save size={13} />Save</button></div>
      </article>)}</div>
    </section>
    <section className="enterprise-card overflow-hidden">
      <div className="border-b border-slate-100 px-5 py-4"><h2 className="text-sm font-bold text-slate-800">APH category rules · 2024-2027</h2><p className="mt-1 text-[10px] text-slate-500">Read-only, source-backed category metadata. NEXORA does not implement AICTE portal selection, notifications, or decision issuance.</p></div>
      <div className="divide-y divide-slate-100">{aphRules.map((item) => <article key={item.key} className="space-y-1 p-4">
        <h3 className="text-xs font-bold text-slate-800">{item.label} · {item.rule_category.replace('_', ' ')}</h3>
        <p className="text-[10px] text-slate-600">Clauses: {item.clauses.join(', ')} · Required: {item.required_documents.join(', ')}</p>
        <p className="text-[10px] text-slate-600">Processing: {item.processing_timeline}</p>
        {item.scope_notes.map((note) => <p key={note} className="text-[10px] text-slate-600">Scope: {note}</p>)}
        {item.mandatory_steps.length > 0 && <p className="text-[10px] text-slate-600">Mandatory: {item.mandatory_steps.join(', ')}</p>}
        {item.conditional_steps.length > 0 && <p className="text-[10px] text-slate-600">Conditional: {item.conditional_steps.join(', ')}</p>}
        <p className="text-[10px] text-slate-600">TER charges: {item.ter_charges === 'no_TER_charges' ? 'No TER charges for closure (APH Clause 2.21)' : item.ter_charges.replace(/_/g, ' ')}</p>
        <ul className="list-disc pl-4 text-[10px] text-slate-500">{item.process_notes.map((note) => <li key={note}>{note}</li>)}</ul>
        <a href={item.source_document} target="_blank" rel="noreferrer" className="inline-block text-[10px] font-semibold text-brand-blue underline">Open official APH</a>
      </article>)}</div>
    </section>
    <section className="grid gap-4 xl:grid-cols-2">
      <article className="enterprise-card p-5"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-50 text-amber-700"><BellRing size={17} /></span><div><h2 className="text-sm font-bold text-slate-800">Reminder intervals</h2><p className="mt-0.5 text-[10px] text-slate-500">Comma-separated example windows in days.</p></div></div><input aria-label="Reminder intervals in days" value={intervals.join(',')} onChange={(e) => setIntervals(e.target.value.split(',').map(Number).filter(Number.isFinite))} className="mt-4 h-10 w-full px-3 text-xs" /><button onClick={saveIntervals} className="mt-3 inline-flex h-9 items-center gap-2 rounded-lg bg-brand-navy px-3 text-[10px] font-semibold text-white transition hover:bg-blue-900"><Save size={13} />Save intervals</button></article>
      <article className="enterprise-card p-5"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50 text-violet-700"><FileText size={17} /></span><div><h2 className="text-sm font-bold text-slate-800">Escalation configuration</h2><p className="mt-0.5 text-[10px] text-slate-500">Edit the configuration as valid JSON.</p></div></div><textarea aria-label="Escalation configuration JSON" rows={6} value={escalation} onChange={(e) => setEscalation(e.target.value)} className="mt-4 w-full p-3 font-mono text-[10px]" /><button onClick={saveEscalation} className="mt-3 inline-flex h-9 items-center gap-2 rounded-lg bg-brand-navy px-3 text-[10px] font-semibold text-white transition hover:bg-blue-900"><Save size={13} />Save configuration</button></article>
    </section>
    <section className="enterprise-card p-5">
      <div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700"><FileText size={17} /></span><div><h2 className="text-sm font-bold text-slate-800">Document categories</h2><p className="mt-0.5 text-[10px] text-slate-500">Maintain categories available for supporting documents.</p></div></div>
      <div className="my-4 flex flex-wrap gap-2">{categories.map((item) => <span key={item.id} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-700">{item.name}<button aria-label={`Delete ${item.name}`} onClick={() => apiDelete(`/admin/document-categories/${item.id}`).then(load).catch((err: Error) => setError(err.message))} className="rounded p-0.5 text-slate-400 transition hover:bg-rose-50 hover:text-rose-700"><Trash2 size={13} /></button></span>)}</div>
      <form onSubmit={addCategory} className="flex flex-col gap-2 sm:flex-row"><input required value={category} onChange={(e) => setCategory(e.target.value)} placeholder="New category" className="h-10 min-w-0 flex-1 px-3 text-xs" /><button className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-brand-navy px-4 text-xs font-semibold text-white transition hover:bg-blue-900">Add category</button></form>
    </section>
  </div>;
}
