# Implementation Plan — NEXORA AICTE

Work happens in place at `e:/SIH26262` (no worktree). The repo is split into `backend/` (FastAPI + SQLAlchemy/SQLite) and `frontend/` (React + TS + Vite + Tailwind). Build the full relational schema up front (Phase 1), then layer behavior, then the frontend, then a final proof gate.

This plan is decomposed into 13 phases, each independently verifiable. Each phase corresponds to one FEAT file under `e:/SIH26262/.agents/tasks/nexora-aicte/features/FEAT-NNN.json` and runs as one implement-and-review loop (coder first, reviewer last; maxIterations 2, pause on max; stop when that phase's `review.json` says APPROVED). Phases run strictly sequentially — every coder shares the one workspace, so concurrent phases would race on git, the DB, and build artifacts.

## Recorded decisions

- **Database:** SQLAlchemy 2.0 + SQLite, `DATABASE_URL` env-configurable (default `sqlite:///./nexora.db`) so it can point at Postgres/Supabase later. Prototype uses `Base.metadata.create_all` on startup (no Alembic). The full 14-table schema is built in Phase 1 so later phases add behavior/seed, not migrations.
- **Auth:** PyJWT + passlib[bcrypt]; RBAC via FastAPI dependencies (`require_roles`, region scope, institution-own scope) enforced backend-side — frontend button hiding is not the security boundary.
- **OCR:** Pluggable and optional. The code `try/except` imports `pytesseract`/`pdfplumber`/`PIL`; if unavailable (expected here), documents are marked Under Verification with a clear note. These libs are NOT in `requirements.txt`. Never auto-declare a document fraudulent; never make a statutory approval decision.
- **Frontend UI:** A hand-rolled component library in `frontend/src/components/ui` (Radix-free, matches the shadcn aesthetic and the navy/white + blue/green theme) instead of shadcn. Reason: the tsconfig uses `moduleResolution: Node` with no path aliases and `isolatedModules`; adding shadcn would require alias + many Radix deps and config churn that risks `tsc -b`. The spec explicitly allows this alternative. Reuse the existing tailwind `brand.*` tokens and `shadow-card`.
- **CORS:** allow `http://localhost:5173` (Vite) calling `:8000` (FastAPI).
- **Scheduler:** APScheduler BackgroundScheduler started on FastAPI startup (Phase 7) for deadline/escalation monitoring — not browser timers.
- **Git:** Phase 1 initializes a git repo at `e:/SIH26262` + `.gitignore` + a baseline commit, so each phase commits and reviewers diff. (No worktree.)
- **Tests:** No test framework exists; verification is build + run + documented curl checks (the spec allows "a backend test or a documented curl check" for the RBAC proof). The frontend gate is `npm run build` (tsc -b && vite build).
- **Dashboard numbers:** Every KPI and chart comes from `/api/dashboard` computed from the DB; the hardcoded numbers in the current `App.tsx`/`main.py` are removed.
- **Demo data:** All fictional, clearly marked; shared dev password `demo1234` for the 5 demo users (documented in README). Reset-demo-data endpoint + admin UI.

## Phases

- [ ] 1. **Backend foundation + full schema + seed + git** (FEAT-001). Project layout, pinned deps, env config, SQLAlchemy engine/session/Base, all 14 models, password+JWT helpers, FastAPI app with CORS for `:5173`, DB auto-init+seed on startup, reference+demo seed, git repo init. Only `/api/health` exposed.
      Files: `backend/requirements.txt`, `backend/.env.example`, `backend/app/{config,database,models,security,seed,main}.py`, root `.gitignore`, git repo.
      Verify: venv install exits 0; `init_db()` prints users>=5, institutions>=6, rules>=8; uvicorn starts and `/api/health` ok; git log shows baseline + FEAT-001 commits.

- [ ] 2. **Auth + RBAC + user management + reset-demo-data** (FEAT-002). JWT login/register, RBAC dependencies (role + region + institution-own scope), admin user CRUD, audit helper, reset-demo-data endpoint, email-configured flag.
      Files: `backend/app/{deps,security}.py` (deps new), `backend/app/schemas/{auth,users}.py`, `backend/app/routers/{auth,users,admin}.py`, `backend/app/services/audit.py`, `backend/app/main.py`.
      Verify: login returns a token for each of the 5 roles; `/api/users` with admin token 200, with institution token 403; reset-demo-data reseeds; AuditLogs rows written.

- [ ] 3. **Applications + configurable workflow engine + dashboard** (FEAT-003). Application CRUD with role-scoped filters/pagination, workflow engine reading `WorkflowRules` (not hardcoded), reason required for every return/rejection, timestamp+user recorded in `ApplicationStage` timeline, deficiency return + resubmit, auto-advance, unauthorized stage changes rejected. Creates `/api/dashboard` (KPIs + charts computed from DB, scoped by role) and `/api/workflow/rules` config.
      Files: `backend/app/schemas/{applications,dashboard}.py`, `backend/app/services/workflow_engine.py`, `backend/app/routers/{applications,workflow,dashboard}.py`, `backend/app/main.py`, `backend/app/seed.py`.
      Verify: create app -> transition with reason -> timeline row; return without reason 400; regional officer A cannot access region B app (403/empty — RBAC curl); `/api/dashboard` numbers equal seeded counts; admin workflow-rule edit changes a subsequent transition.

- [ ] 4. **Documents + OCR + categories** (FEAT-004). Private upload (PDF/JPG/PNG, type+size validation), metadata, pluggable OCR (degrades to Under Verification), authorized verification with remarks, document-category CRUD, Expired Documents KPI. Never public URLs; never a fraud verdict.
      Files: `backend/app/schemas/documents.py`, `backend/app/services/ocr.py`, `backend/app/routers/documents.py`, `backend/app/routers/admin.py` (extend categories), `backend/app/models.py` (add DocumentCategory), `backend/app/main.py`, `backend/app/seed.py`.
      Verify: upload PDF/PNG -> 201 under_verification; retrieve with own token 200, other institution 403; .txt 415; 11MB 413; officer verify -> AuditLogs; `/api/admin/document-categories` lists 6; Expired Documents KPI matches count.

- [ ] 5. **Compliance + undertakings + lease/expiry + reminder config** (FEAT-005). Time-bound undertakings with due dates, evidence upload, officer verify/deficiency, completion tracking. Lease/expiry dashboard buckets (Valid / Expiring Soon / Expired / Renewal Awaited / Renewal Under Verification) computed from expiry_date vs configurable reminder intervals (examples only). Renewal creates a replacement doc. Compliance Due Soon KPI + compliance completion chart.
      Files: `backend/app/schemas/compliance.py`, `backend/app/services/expiry.py`, `backend/app/routers/{compliance,lease}.py`, `backend/app/routers/admin.py` (reminder intervals), `backend/app/routers/dashboard.py` (extend), `backend/app/main.py`, `backend/app/seed.py`.
      Verify: due-soon compliance record days_remaining correct; `/api/lease/dashboard` buckets match seeded docs; renewal upload flips bucket to Renewal Under Verification; reminder-interval change changes Expiring Soon set; Compliance Due Soon KPI + chart present.

- [ ] 6. **EVC scheduling** (FEAT-006). EVC appointments, calendar + table views (date range/status filters), scheduling for apps in the EVC queue, completion with findings+recommendation that advances the app past the EVC stage via the workflow engine. Awaiting EVC + Awaiting Committee Review KPIs.
      Files: `backend/app/schemas/evc.py`, `backend/app/routers/evc.py`, `backend/app/services/workflow_engine.py` (extend EVC completion), `backend/app/routers/dashboard.py` (extend), `backend/app/main.py`, `backend/app/seed.py`.
      Verify: schedule -> 201; `/api/evc` calendar+table; complete -> app advances; scheduling a non-EVC-stage app rejected; KPIs match counts.

- [ ] 7. **Notifications + escalation + scheduled monitor** (FEAT-007). In-app notification center (event_type, related_id, recipient, created_at, due_date, is_read, action_link) with event hooks across workflow/compliance/lease/EVC/verification. Email labeled unconfigured when SMTP empty. APScheduler monitor creates overdue alerts + escalations at configurable levels 1/2/3; manual `run-monitor` for demos. Overdue Cases KPI + upcoming-deadlines chart.
      Files: `backend/app/schemas/notifications.py`, `backend/app/services/{notifications_service,escalation,scheduler}.py`, `backend/app/routers/notifications.py`, `backend/app/routers/admin.py` (escalation-config), `backend/app/routers/dashboard.py` (extend), `backend/app/main.py` (start scheduler), `backend/app/seed.py`.
      Verify: a transition creates a recipient notification; `run-monitor` on the scenario-6 overdue app creates an overdue notification + level-1 escalation; unread-count correct; email reported unconfigured; KPI + chart present.

- [ ] 8. **Reports (CSV) + audit logs + finalized dashboard** (FEAT-008). Seven CSV reports computed from DB (pendency, region-performance, EVC, compliance, documents, overdue, decisions) with filters + role scope. Audit log query endpoint (read-only, role-scoped). Confirm all 8 KPIs + 6 charts present and DB-computed.
      Files: `backend/app/schemas/reports.py`, `backend/app/routers/{reports,audit}.py`, `backend/app/services/audit.py` (coverage check), `backend/app/routers/dashboard.py` (finalize), `backend/app/main.py`.
      Verify: all 7 CSVs non-empty for seeded data; audit row appears after a transition with prev/new status+reason; dashboard has 8 KPIs + 6 charts matching DB counts; regional officer CSV scoped to their region.

- [ ] 9. **Frontend foundation + auth + Main Dashboard** (FEAT-009). Routing, API client (Bearer token + 401 logout), AuthContext, role-based route guards, AppLayout (role-aware sidebar nav), hand-rolled UI component library, Login/Register (page 1), Main Dashboard (page 2) with live KPIs + 6 charts + filters. Replace the single `App.tsx`; keep `npm run build` passing.
      Files: `frontend/src/{App.tsx,routes.tsx,api/client.ts,auth/AuthContext.tsx}`, `frontend/src/components/ui/*`, `frontend/src/components/layout/AppLayout.tsx`, `frontend/src/pages/{Login,Register,Dashboard}.tsx`, `frontend/.env.example`.
      Verify: `npm run build` 0 errors; login as each role -> role dashboard with KPIs/charts from `/api/dashboard` (regional officer sees only their region); filters re-query; no hardcoded numbers.

- [ ] 10. **Frontend applications + documents** (FEAT-010). Applications List (search/filter/sort/pagination), Application Details + full timeline, New Application Form, Document Upload & Verification (pages 3-6). Role-aware; return/reject requires a reason; loading/empty/error + confirm dialogs + success toasts.
      Files: `frontend/src/pages/{ApplicationsList,ApplicationDetail,NewApplication,Documents}.tsx`, `frontend/src/routes.tsx`, `frontend/src/components/layout/AppLayout.tsx`.
      Verify: `npm run build` 0 errors; create app -> appears; return for deficiency (reason required) -> institution resubmits -> timeline updates; upload PDF -> Under Verification -> officer verifies -> download; .txt/oversize blocked.

- [ ] 11. **Frontend EVC + compliance + lease + notifications + reports** (FEAT-011). EVC Scheduling (calendar + table), Compliance Management, Lease & Document Expiry, Notifications center, Reports & Analytics with CSV downloads (pages 7-11).
      Files: `frontend/src/pages/{EVCScheduling,Compliance,LeaseExpiry,Notifications,Reports}.tsx`, `frontend/src/routes.tsx`, `frontend/src/components/layout/AppLayout.tsx`.
      Verify: `npm run build` 0 errors; schedule+complete EVC advances app; compliance due-soon/overdue badges + evidence; lease buckets + renewal; notifications mark-read + unread badge + Email-unconfigured banner; each of 7 CSVs downloads (regional officer scoped).

- [ ] 12. **Frontend user mgmt + workflow config + audit + help** (FEAT-012). User & Role Management, Workflow Configuration, Audit Logs (read-only), Help & System Info (pages 12-15). Reset-demo-data UI; configurable rules/intervals/escalation/categories.
      Files: `frontend/src/pages/{UserManagement,WorkflowConfig,AuditLogs,Help}.tsx`, `frontend/src/routes.tsx`, `frontend/src/components/layout/AppLayout.tsx`.
      Verify: `npm run build` 0 errors; admin create/deactivate user persists; reset-demo-data reseeds; workflow-rule flag change changes a transition; reminder/escalation config persists; audit read-only + scoped; Help lists roles + safeguards + 6 scenarios.

- [ ] 13. **Final verification gate** (FEAT-013). README (setup + 5 demo logins + 6 scenario click paths + RBAC curl + safeguards), verify both `.env.example` files (no secrets), run the full proof gate: `npm run build`; uvicorn start + `/docs` + DB seed; 5 role logins land on role dashboards; RBAC curl; all 6 scenarios reproducible; reset-demo-data. Gap-fix only; behavior-changing changes require a warning to the user.
      Files: `e:/SIH26262/README.md`, `e:/SIH26262/backend/.env.example`, `e:/SIH26262/frontend/.env.example` (verify).
      Verify: all proof gates green (build, uvicorn/docs/seed, 5 logins, RBAC curl, 6 scenarios, reset-demo-data).

## Digest

Workspace root `e:/SIH26262`. No existing tests. The frontend build is the TS gate; the backend gate is uvicorn start + curl checks. Pin exact versions; do not add optional OCR libs to `requirements.txt`. The existing `App.tsx` and `main.py` are fully replaced/extended — see below.

**Existing files touched (blocks to change):**

- `backend/app/main.py` — current: `FastAPI` + `CORSMiddleware(allow_origins=['*'])` + `/api/health`, `/api/dashboard`, `/api/applications`, `/api/compliance` returning hardcoded JSON. FEAT-001: tighten CORS to `Settings.CORS_ORIGINS`, add startup `init_db()`, remove the 3 hardcoded endpoints. FEAT-002+: include routers as each phase lands them; FEAT-007 starts the scheduler. Keep `/api/health`.
- `backend/requirements.txt` — current 3 pins. FEAT-001 appends pinned sqlalchemy/pydantic-settings/pydantic[email]/email-validator/pyjwt/passlib/bcrypt/apscheduler. No further edits.
- `backend/app/__init__.py` — unchanged (package marker).
- `frontend/src/App.tsx` — current: single hardcoded dashboard calling the 3 endpoints. FEAT-009: replace with `<Routes>` inside `AuthProvider`. The old JSX is deleted entirely.
- `frontend/src/main.tsx` — current: `BrowserRouter` + `<App/>`. Keep (FEAT-009 may wrap `AuthProvider` here or in App).
- `frontend/src/index.css` — keep (Inter font, gradient bg, scrollbar). FEAT-009 may add a few component utility classes.
- `frontend/tailwind.config.js` — keep brand tokens + `shadow-card`. FEAT-009 may extend with chart/semantic colors only if needed.
- `frontend/vite.config.ts` — keep (host `0.0.0.0`, port 5173).
- `frontend/package.json` — unchanged (all needed deps already present; add NO new frontend deps). `npm run build` = `tsc -b && vite build`.
- `frontend/tsconfig.app.json` — unchanged (strict, `isolatedModules` -> use `import type`, `moduleResolution: Node`, no aliases, `noEmit`).

**New files by phase** (all grounded in the FEAT steps above): backend `app/{config,database,models,security,seed,deps}.py`, `app/schemas/*`, `app/routers/*`, `app/services/*`, `backend/.env.example`, root `.gitignore`; frontend `src/{routes.tsx,api/client.ts,auth/AuthContext.tsx}`, `src/components/ui/*`, `src/components/layout/AppLayout.tsx`, `src/pages/*.tsx`, `frontend/.env.example`; root `README.md`.

**What passes today (before any change):**
- Frontend: `cd frontend && npm run build` — passes (the current single `App.tsx` compiles; node_modules installed).
- Backend: no build; `uvicorn app.main:app` starts and `/api/health` returns ok, but `/api/dashboard|applications|compliance` return hardcoded JSON and there is no DB/auth.

**Per-phase verification** uses the real commands in each FEAT's `verification` array (venv install + uvicorn + curl for backend; `npm run build` + dev-server click-through for frontend). The final gate (FEAT-013) runs the complete proof checklist.

## Workflow restructuring

This work decomposes into separable phases (each is a coherent subsystem with its own verification). I restructured the remaining workflow into one implement-and-review loop per phase (13 loops), plus the final verification phase as the 13th loop, via `update_workflow replace_remaining`. Each loop: a coder step then a reviewer step, `maxIterations: 2`, `onMaxIterations: pause`, `stopCondition` = fileCheck on `e:/SIH26262/.agents/tasks/nexora-aicte/FEAT-NNN/review.json` for `verdict: APPROVED`. The reviewer writes that file every iteration with `{"verdict":"APPROVED"|"CHANGES_REQUESTED","findings":[...],"reviewDoc":"<path>"}` and calls `send_message` severity `success`. The coder reads the FEAT file + `context.json` first, implements/runs that FEAT's verification, commits with the commands+results in the message, and on iteration 2 fixes the reviewer's findings (calling `send_message` severity `warning` and waiting if a fix would change user-visible behavior). Reviewers read the diff + the coder's recorded evidence and do not re-run the suites.
