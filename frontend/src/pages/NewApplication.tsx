import { ArrowLeft, ArrowRight, Building2, CheckCircle2, FileText, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiGet, apiPost } from '../api/client';
import { useAuth } from '../auth/AuthContext';

type WorkflowPath = { key: string; label: string; description: string; stages: string[]; is_demo_example: boolean };
type WorkflowSuggestion = { key: string; label: string; description: string; reason: string; is_demo_suggestion: boolean };
type AphRule = {
  key: string; label: string; workflow_path: string; rule_category: string;
  clauses: string[]; mandatory_steps: string[]; conditional_steps: string[];
  required_documents: string[]; processing_timeline: string; source_document: string;
  minimum_core_courses: number | null; ter_charges: string; process_notes: string[]; scope_notes: string[];
};

export default function NewApplication() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [type, setType] = useState('');
  const [workflowPaths, setWorkflowPaths] = useState<WorkflowPath[]>([]);
  const [aphRules, setAphRules] = useState<AphRule[]>([]);
  const [aphRuleKey, setAphRuleKey] = useState('');
  const [workflowPath, setWorkflowPath] = useState('scrutiny_evc_sac_shc');
  const [programArea, setProgramArea] = useState('');
  const [coreCourseCount, setCoreCourseCount] = useState('');
  const [workflowSuggestion, setWorkflowSuggestion] = useState<WorkflowSuggestion | null>(null);
  const [workflowWasManuallyChanged, setWorkflowWasManuallyChanged] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const institutionLinked = Boolean(user?.institution_id);
  const selectedRule = aphRules.find((rule) => rule.key === aphRuleKey);
  const demoOnly = aphRuleKey === 'demo_only';
  const applicationType = selectedRule?.label || type;
  const applicationTypeReady = applicationType.trim().length >= 2;
  const coreCountReady = !selectedRule?.minimum_core_courses
    || programArea === 'other'
    || (programArea === 'engineering_technology'
      && Number(coreCourseCount) >= selectedRule.minimum_core_courses);
  const routeReady = Boolean(selectedRule || demoOnly) && (!demoOnly || Boolean(workflowPaths.length && workflowPath));
  const readyChecks = Number(institutionLinked) + Number(applicationTypeReady) + Number(routeReady) + Number(coreCountReady);

  useEffect(() => {
    Promise.all([
      apiGet<WorkflowPath[]>('/workflow/paths'),
      apiGet<AphRule[]>('/workflow/aph-rules'),
    ])
      .then(([paths, rules]) => { setWorkflowPaths(paths); setAphRules(rules); })
      .catch((err: Error) => setError(err.message));
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const result = await apiPost<{ id: string }>('/applications', {
        application_type: applicationType,
        workflow_path: demoOnly ? workflowPath : undefined,
        aph_rule_key: demoOnly ? undefined : aphRuleKey,
        program_area: selectedRule?.minimum_core_courses ? programArea : undefined,
        core_course_count: selectedRule?.minimum_core_courses && coreCourseCount
          ? Number(coreCourseCount)
          : undefined,
      });
      navigate(`/applications/${result.id}`);
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not create application'); }
    finally { setBusy(false); }
  }

  async function suggestRoute() {
    if (!demoOnly || type.trim().length < 2) return;
    try {
      const suggestion = await apiPost<WorkflowSuggestion>('/workflow/suggest', {
        application_type: type.trim(),
      });
      setWorkflowSuggestion(suggestion);
      if (!workflowWasManuallyChanged) setWorkflowPath(suggestion.key);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not suggest a demo workflow');
    }
  }

  return <div className="mx-auto max-w-3xl space-y-5">
    <Link to="/applications" className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-brand-blue"><ArrowLeft size={14} />Back to applications</Link>
    <header><p className="text-[11px] font-bold uppercase tracking-[.13em] text-brand-blue">Application management</p><h1 className="page-title mt-1 text-2xl font-bold text-brand-navy md:text-[28px]">Start a new application</h1><p className="mt-1 text-sm text-slate-500">Submit an application for your registered institution.</p></header>
    <section className="enterprise-card overflow-hidden">
      <div className="border-b border-slate-100 bg-slate-50/60 px-5 py-4"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-brand-blue"><FileText size={17} /></span><div><h2 className="text-sm font-bold text-slate-800">Application details</h2><p className="text-[10px] text-slate-500">You can add supporting documents after submission.</p></div></div></div>
      <form onSubmit={submit} className="space-y-5 p-5 md:p-7">
        <div className="flex items-start gap-3 rounded-xl border border-blue-100 bg-blue-50/60 p-4"><Building2 size={17} className="mt-0.5 shrink-0 text-brand-blue" /><p className="text-xs leading-5 text-slate-600">Your institution and region are securely linked to your account and will be included automatically.</p></div>
        <label className="block text-xs font-semibold text-slate-700">APH 2024-2027 application category
          <select required value={aphRuleKey} onChange={(event) => { setAphRuleKey(event.target.value); setWorkflowSuggestion(null); }} className="mt-2 h-11 w-full px-3.5 text-sm">
            <option value="">Select an application category</option>
            {aphRules.map((rule) => <option key={rule.key} value={rule.key}>{rule.label}</option>)}
            <option value="demo_only">Demo-only example route (not an APH category)</option>
          </select>
        </label>
        {selectedRule && <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-4 text-[11px] leading-5 text-slate-700">
          <p><b>APH clauses:</b> {selectedRule.clauses.join(', ')}</p>
          <p><b>Processing window:</b> {selectedRule.processing_timeline} (no fixed day-count is inferred).</p>
          <p><b>Required document:</b> {selectedRule.required_documents.join(', ')}</p>
          <p><b>TER charges:</b> {selectedRule.ter_charges === 'no_TER_charges' ? 'No TER charges for closure (APH Clause 2.21)' : selectedRule.ter_charges.replace(/_/g, ' ')}</p>
          {selectedRule.scope_notes.map((note) => <p key={note}><b>Scope:</b> {note}</p>)}
          {selectedRule.mandatory_steps.length > 0 && <p><b>Mandatory steps:</b> {selectedRule.mandatory_steps.join(', ')}</p>}
          {selectedRule.conditional_steps.length > 0 && <p><b>Conditional steps:</b> {selectedRule.conditional_steps.join(', ')}</p>}
          {selectedRule.process_notes.map((note) => <p key={note} className="mt-1 text-slate-500">• {note}</p>)}
          <a className="mt-1 inline-block font-semibold text-brand-blue underline" href={selectedRule.source_document} target="_blank" rel="noreferrer">Open official APH source</a>
        </div>}
        {selectedRule?.minimum_core_courses && <div className="space-y-3 rounded-xl border border-slate-200 p-4">
          <label className="block text-xs font-semibold text-slate-700">Programme area
            <select required value={programArea} onChange={(event) => setProgramArea(event.target.value)} className="mt-2 h-10 w-full px-3 text-xs">
              <option value="">Select programme area</option>
              <option value="engineering_technology">Engineering and Technology</option>
              <option value="other">Other</option>
            </select>
          </label>
          {programArea === 'engineering_technology' && <label className="block text-xs font-semibold text-slate-700">Existing core courses
            <input required type="number" min={selectedRule.minimum_core_courses} value={coreCourseCount} onChange={(event) => setCoreCourseCount(event.target.value)} className="mt-2 h-10 w-full px-3 text-xs" />
            <span className="mt-1 block text-[10px] font-normal text-slate-500">Clause 2.6 requires at least {selectedRule.minimum_core_courses} core courses for this Engineering and Technology category.</span>
          </label>}
        </div>}
        {demoOnly && <>
          <label className="block text-xs font-semibold text-slate-700">Illustrative workflow path
            <select required value={workflowPath} onBlur={() => void suggestRoute()} onChange={(event) => { setWorkflowPath(event.target.value); setWorkflowWasManuallyChanged(true); }} className="mt-2 h-11 w-full px-3.5 text-sm">
              {workflowPaths.map((path) => <option key={path.key} value={path.key}>{path.label}</option>)}
            </select>
            <span className="mt-1.5 block text-[10px] font-normal text-slate-500">{workflowPaths.find((path) => path.key === workflowPath)?.description}</span>
            {workflowSuggestion && <span role="status" className="mt-1 block text-[10px] font-medium text-emerald-700">Suggested for “{type}”: {workflowSuggestion.label}. {workflowSuggestion.reason}{workflowWasManuallyChanged ? ' Your manual selection is kept.' : ''}</span>}
            <span className="mt-1 block text-[10px] font-normal text-amber-700">Illustrative SIH prototype route; not an official AICTE workflow determination.</span>
          </label>
          <label className="block text-xs font-semibold text-slate-700">Demo application type<input required minLength={2} maxLength={100} value={type} onChange={(event) => { setType(event.target.value); setWorkflowSuggestion(null); setWorkflowWasManuallyChanged(false); }} placeholder="e.g. New Institution, Renewal, Program Expansion" className="mt-2 h-11 w-full px-3.5 text-sm" /></label>
        </>}
        <section aria-label="Application readiness checklist" className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
          <div className="flex items-center justify-between gap-3"><div><h2 className="text-xs font-bold text-slate-800">Ready to submit?</h2><p className="mt-1 text-[10px] text-slate-500">A quick check before this record enters the workflow.</p></div><span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-semibold text-brand-blue">{readyChecks}/4 ready</span></div>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            <li className="flex items-center gap-2 text-[11px] text-slate-600"><CheckCircle2 size={14} className={institutionLinked ? 'text-emerald-600' : 'text-slate-300'} />Institution account {institutionLinked ? 'is linked' : 'needs to be linked'}</li>
            <li className="flex items-center gap-2 text-[11px] text-slate-600"><CheckCircle2 size={14} className={applicationTypeReady ? 'text-emerald-600' : 'text-slate-300'} />Application type {applicationTypeReady ? 'entered' : 'required'}</li>
            <li className="flex items-center gap-2 text-[11px] text-slate-600"><CheckCircle2 size={14} className={routeReady ? 'text-emerald-600' : 'text-slate-300'} />APH category or demo route {routeReady ? 'selected' : 'required'}</li>
            <li className="flex items-center gap-2 text-[11px] text-slate-600"><CheckCircle2 size={14} className={coreCountReady ? 'text-emerald-600' : 'text-slate-300'} />Clause 2.6 course minimum {coreCountReady ? 'checked' : 'not met'}</li>
          </ul>
          {!institutionLinked && <p role="alert" className="mt-3 text-[10px] font-medium text-rose-700">Ask a workspace administrator to link your institution before submitting.</p>}
          <p className="mt-3 border-t border-slate-200 pt-3 text-[10px] leading-5 text-slate-500"><b>Next:</b> After creation, attach relevant supporting files from Documents. The workspace tracks file review status; it does not determine official eligibility or document completeness.</p>
        </section>
        <div className="flex items-start gap-2 rounded-lg bg-slate-50 p-3 text-[10px] leading-5 text-slate-500"><ShieldCheck size={14} className="mt-0.5 shrink-0 text-emerald-600" />Submitting creates a traceable NEXORA record. NEXORA does not submit to AICTE or make approval decisions.</div>
        {error && <p role="alert" className="rounded-lg border border-rose-100 bg-rose-50 p-3 text-xs text-rose-700">{error}</p>}
        <div className="flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-4"><Link to="/applications" className="inline-flex h-10 items-center rounded-lg border border-slate-200 px-4 text-xs font-semibold text-slate-600 hover:bg-slate-50">Cancel</Link><button disabled={busy || !institutionLinked || !applicationTypeReady || !routeReady || !coreCountReady} className="inline-flex h-10 items-center gap-2 rounded-lg bg-brand-blue px-4 text-xs font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50">{busy ? 'Submitting…' : 'Submit application'}{!busy && <ArrowRight size={14} />}</button></div>
      </form>
    </section>
    <div className="flex items-center gap-2 text-[10px] text-slate-400"><CheckCircle2 size={13} className="text-emerald-500" />Application activity is recorded for transparent review.</div>
  </div>;
}
