<div align="center">

<img src="./assets/nexora-readme-banner.svg" alt="NEXORA — AICTE Approval and Compliance Workspace" width="100%" />

<br />

[![React](https://img.shields.io/badge/React-18.3-149ECA?logo=react&logoColor=white)](https://react.dev/)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)
![FastAPI](https://img.shields.io/badge/API-FastAPI-0.162-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-2.0-8B0000?logo=sqlalchemy&logoColor=white)
![Database](https://img.shields.io/badge/DB-SQLite%20%7C%20PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Status](https://img.shields.io/badge/Status-Fictional%20prototype-52627A)

<br />

[🚀 Quick start](#-quick-start) · [🎬 Demo accounts](#-demo-accounts--scenarios) · [🧱 Architecture](#-tech-stack--architecture) · [⚙️ Configuration](#️-configuration) · [🔒 Safeguards](#-security--limitations)

</div>

---

## 🚀 Quick start

Already installed and configured? Start the app in two terminals:

**Terminal 1 — backend** (`http://localhost:8000`)
```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend** (`http://localhost:5173`)
```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and sign in with `admin@nexora-demo.in` / `demo1234`.

> **First run?** Follow [Run locally](#-run-locally) to create the Python environment and configure `backend/.env` first.
>
> Prefer Docker? Once `.env.production` is configured, the full stack (PostgreSQL + backend + frontend) runs on `:8080`:
> ```powershell
> docker compose --env-file .env.production up -d --build
> ```
> See [🐳 Production stack](#-run-locally) for setup.

---

## 📋 At a glance

| What it helps with | What teams can do |
|---|---|
| **Applications** | Submit, search and track cases through configurable review stages. |
| **Documents & compliance** | Upload evidence, review status, follow deadlines and monitor lease renewals. |
| **EVC operations** | Coordinate visits, committee assignments, findings and recommendations. |
| **Insights & accountability** | View role-scoped dashboards, reports, notifications and audit history. |
| **APH workflow reference** | Choose supported Approval Process Handbook 2024–2027 categories for a documented, prototype-only route. |

Built with **React + TypeScript**, **FastAPI** and **SQLAlchemy**. The app includes a public product landing page, sign-in and institution access requests, a role-aware workspace, and a help assistant available across pages.

### Quick demo sign-in

| Email | Password |
|---|---|
| `admin@nexora-demo.in` | `demo1234` |

Use these **local prototype credentials only**. More role-specific accounts and guided demo scenarios are listed in [🎬 Demo accounts & scenarios](#-demo-accounts--scenarios).

---

## 📑 Contents

<details open>
<summary><strong>Browse the guide</strong></summary>

- [What is NEXORA?](#-what-is-nexora)
- [Tech stack & architecture](#-tech-stack--architecture)
- [What is included](#-what-is-included)
- [AI and automation scope](#-ai-and-automation-scope)
- [Roles and access](#-roles-and-access)
- [Application workflow](#-application-workflow)
- [Demo accounts and scenarios](#-demo-accounts--scenarios)
- [Run locally](#-run-locally)
- [Configuration](#️-configuration)
- [Public AICTE data integration](#-public-aicte-data-integration)
- [Project structure and screens](#-project-structure--screens)
- [Security and limitations](#-security--limitations)
- [Useful commands](#-useful-commands)

</details>

## 🧭 What is NEXORA?

NEXORA brings the main steps of an institutional approval and compliance journey into one responsive workspace. Institutions can submit applications and supporting evidence; officers can review records and move them through configurable stages; EVC committees can coordinate visits and submit findings; administrators can manage access and prototype workflow settings.

The interface uses a responsive enterprise design with a deep-navy navigation rail, teal/cyan accents, warm neutral workspace surfaces and differentiated KPI cards. Dashboard metrics and operational records come from the backend rather than presentation-only hardcoded totals. Light and dark themes, responsive navigation and accessible state colors are supported.

### Interface at a glance

- **Public entry:** product overview, application journey, team roles and a clear sign-in path.
- **Workspace shell:** collapsible dark-navy navigation, grouped pages, active-route marker, sticky breadcrumb/search/notification bar, profile menu and theme toggle.
- **Dashboard:** role-scoped KPI cards, application status, regional pendency, monthly submissions, workflow stages, compliance progress, upcoming/overdue action queue and recent applications.
- **Application detail:** route-specific timeline, supporting documents, scrutiny/compliance history and authorized workflow actions.
- **Responsive behavior:** desktop sidebar collapses; smaller screens use a navigation drawer and horizontally scrollable data tables where needed.

The interface is an operational view of the NEXORA prototype; visual status indicators and dashboard counts are not AICTE decisions or official data unless a source is explicitly identified.

**A typical journey:** an institution submits a case → an authorized officer reviews it → an EVC visit can be coordinated → the configured workflow records progress and outcome. Each account sees the records and actions allowed for its role.

## 🧱 Tech stack & architecture

| Layer | Stack |
|---|---|
| **Frontend** | React 18.3, TypeScript 5.6, Vite 5.4, React Router 6.28, Tailwind CSS 3.4, Recharts 2.13, Lucide icons |
| **Backend** | FastAPI 0.162, Uvicorn 0.30, SQLAlchemy 2.0, Pydantic 2.9 / pydantic-settings 2.6, PyJWT 2.15, Passlib + bcrypt, APScheduler 3.10, SlowAPI rate limiting |
| **Database** | SQLite (local prototype) · PostgreSQL via `psycopg` 3.2 (production) |
| **Runtime** | Python 3.12 · Node.js + npm |

```mermaid
flowchart TB
    FE["React SPA<br/>(Vite dev :5173 / Nginx :8080)"]
    PROXY["Vite dev proxy<br/>/api → 127.0.0.1:8000"]
    API["FastAPI :8000"]
    DB[("Database<br/>SQLite / PostgreSQL")]
    OAI["OpenAI-compatible<br/>chat completions"]

    FE -->|same-origin /api| PROXY --> API
    API --> DB
    API -.->|only if AI_CHAT_API_KEY set| OAI
```

**Request flow**
- The browser loads the React SPA and calls the API on the **same-origin `/api` path**. In development, Vite proxies `/api/*` to `http://127.0.0.1:8000`; in the Docker stack, Nginx routes `/api/*` to the backend service.
- Every protected route authenticates the JWT bearer token via `app/deps.py` and enforces **role + record-scope** checks (region, institution, application ownership).
- The **assistant** route (`/api/assistant`) calls an OpenAI-compatible chat-completions endpoint **only when `AI_CHAT_API_KEY` is set**; otherwise it returns 503 and the frontend falls back to its local workspace guide. The key never leaves the backend.
- Scheduled jobs (deadline monitor every 5 min; optional public-data sync) run via APScheduler inside the backend lifespan.

## 📦 What is included

### Workspace and analytics
- Role-aware navigation, collapsible dark desktop sidebar, mobile drawer, breadcrumbs, global application search, profile menu and notification count.
- NEXORA prototype dashboard with visually differentiated KPI cards, status and regional charts, monthly trends, workflow stages, compliance progress, and a priority queue for overdue and upcoming work.
- Separate Live AICTE Data Dashboard for public institution/approval data; it never merges official public data with prototype application records.
- Application search, filters, sorting, pagination and CSV export.
- Reports for application pendency, regional performance, EVC appointments, compliance, document validity, overdue actions and decisions.
- Application-type-based suggestions for illustrative workflow routes, with an editable manual override.
- EVC-specific upcoming-deadline reminders and overdue escalations for both EVC stage deadlines and scheduled visits.
- AICTE public institution dashboard with source attribution, synchronization status and last-successful-sync time.

### Application and operations
- Institution application submission with a readiness checklist, plus application evidence-review progress and an application-linked upload shortcut.
- Configurable workflow transitions, stage history, scrutiny observations, remarks and record-level access checks.
- Document upload and review, private authenticated downloads, verification status, expiry information and optional advisory OCR.
- Compliance undertakings, evidence submission, deadlines, verification and deficiency remarks.
- Lease expiry and renewal tracking.
- EVC scheduling, committee assignments, visit findings, recommendations and inspection history.
- In-app notifications, unread indicators, activity history and audit logs.

### Administration and support
- User and role administration, regional assignment, activation/deactivation and institution association.
- Configurable example workflow rules, reminder windows, escalation settings and document categories.
- Administrator-triggered deadline monitor and a clearly labelled demo-data reset.
- Role-aware guided demo scenarios, role descriptions and safeguards.
- Public landing page, split-screen sign-in, institution access requests and a help assistant available across public and signed-in pages.

### Visual design and usability
- Responsive layouts for desktop, laptop, tablet and mobile.
- Deep-navy navigation with teal/cyan primary accents, warm neutral workspace surfaces, and amber/rose/emerald status colors.
- Distinct KPI-card accents, Recharts analytics, Lucide iconography, accessible form labels, visible focus states and reduced-motion support.
- Light and dark themes, with persistent theme selection.
- Clear empty, error and loading states across operational pages.

## 🤖 AI and automation scope

NEXORA is a workflow prototype — not an AICTE decision system. Here is what the assistant and automation actually do:

| Capability | Scope |
|---|---|
| **Help assistant** | Provides a local workspace guide. Optional open-ended replies use an OpenAI-compatible endpoint only when `AI_CHAT_API_KEY` is configured; signed-in chat messages and recent context are then sent to the provider. The assistant cannot inspect records or perform actions. |
| **Workflow and deadlines** | Uses configured rules for stage routing, reminders, escalations and dashboard indicators. These are not AI predictions or official timelines. |
| **Document text extraction** | Optional OCR can help a person review a file; it does not verify authenticity or make decisions. OCR dependencies/engine are optional and may be unavailable. |
| **Approval decisions** | No machine-learning approval model or automated fraud detector is included. Human review remains essential. |

Do not send passwords, personal information or confidential institutional records to the assistant. The public AICTE data screen remains empty until an authorized, verified Open Government Data source is configured. Demo applications and institutions are fictional and must not be presented as live AICTE records.

## 👥 Roles and access

Every account has one of the following roles. Navigation visibility is not the security boundary: the API also authenticates requests and checks role and record scope.

| Role | Main responsibilities | Data and action scope |
|---|---|---|
| **Administrator (`admin`)** | Manage accounts and roles; configure example workflow rules, reminders, escalation and document categories; run the deadline monitor; reset demo data. | Broad workspace administration and access to system tools. |
| **Regional Officer (`regional_officer`)** | Review applications in the assigned region; record scrutiny and workflow actions; schedule EVC visits; review documents and compliance evidence. | Application and operational records are scoped to the officer's region. |
| **Bureau Officer (`bureau_officer`)** | Coordinate cross-region workflow review and decisions; work with EVC appointments; review documents and compliance; view reports and audit history. | Broad operational scope, subject to the permissions of each action and workflow stage. |
| **EVC / Committee (`evc_committee`)** | Work with applications in the EVC queue; view scheduled visits; record visit findings and recommendations. | Restricted to EVC-stage work; no document-review or compliance access. |
| **Institution (`institution`)** | Submit and resubmit applications; upload supporting documents; submit compliance evidence; view owned records and notifications. | Limited to the institution linked to the signed-in account. |

### Page access at a glance

| Page | Access |
|---|---|
| Dashboard, application list and details | All signed-in roles; records are scoped by role and ownership. |
| New application | Institution. |
| Document review | Signed-in roles, with role- and record-specific restrictions. |
| EVC scheduling | Administrator, Regional Officer, Bureau Officer and EVC / Committee. |
| Compliance and lease management | Available in the workspace; API actions and records remain permission-scoped. |
| Notifications, reports and help | Signed-in users; report data respects the caller's access scope. |
| User management and workflow configuration | Administrator. |
| Audit logs | Administrator and Bureau Officer. |

## 🔀 Application workflow

The seeded demo workflow contains eight configurable example stages:

1. **Application Submission**
2. **Initial Scrutiny**
3. **Deficiency Check**
4. **EVC Scheduling**
5. **EVC Completion**
6. **SAC / SHC / Committee Stage**
7. **Authorised Decision**
8. **Final Application Status**

Authorized users can advance a case according to its configured stage rules. Officers can return or reject a case with a reason; the owning institution can resubmit a returned application. Transitions update the stage timeline, status and applicable deadline, create an audit entry, and notify relevant users.

The stage names, deadlines, reminder intervals and escalation settings are prototype configuration examples. They are **not official AICTE rules or statutory timelines**.

When creating an application, choose a source-backed **APH 2024–2027** category to use its category route and processing window. The separate **Demo-only example route** preserves the illustrative paths (**Only Scrutiny**, **Scrutiny + EVC**, **EVC + SAC/SHC**, **Scrutiny + EVC + SAC/SHC**, or **Only EVC**) and is not an APH determination.

### APH 2024–2027 implementation scope

The rules below are mapped from the [official AICTE Approval Process Handbook 2024–2027](https://aicte.gov.in/sites/default/files/APH%20Final.pdf), principally Clauses 1.8, 1.9, 2.5–2.7, 2.21, 2.24, 2.25, and Tables 2.2–2.3. Each APH application stores its source URL, handbook period, rule category, clause references, required documents, mandatory/conditional steps, processing window, and effective status.

| APH category | NEXORA route / requirements | Processing window |
|---|---|---|
| EoA based on self-disclosure | Application → Self-Disclosure → Processing; Annexure-2; no standard Scrutiny, EVC, or SAC/SHC stage | As per AICTE Public Notice |
| Increase in intake / additional courses | Annexure-2; mandatory Scrutiny and EVC; SAC/SHC is conditional on previous processing outcome; Clause 2.6 Engineering & Technology minimum is captured as an applicant assertion | As per AICTE Public Notice |
| New programme / level | Annexure-2; mandatory Scrutiny and EVC; conditional SAC/SHC; Clause 2.7 directs new courses under the programme to Clause 2.6 | As per AICTE Public Notice |
| Change of institution name | Annexure-2; Scrutiny; no standard EVC | As per AICTE Public Notice |
| Merger | Annexure-2; Scrutiny and EVC; conditional SAC/SHC; Table 2.2 scope is same campus/city | As per AICTE Public Notice |
| Change of site/location | Annexure-2; Scrutiny and EVC; conditional SAC/SHC; campus shifting is noted as during vacation time | Year-round |
| Closure of institution | Annexure-2; Scrutiny; no standard EVC; no TER charges under Clause 2.21 | Year-round |
| Other supported Table 2.2 categories | Change of bank details, trust/society/company name, closure of programme/course | Year-round |
| ODL / Online learning | Annexure-2; Table 2.3 route metadata | Year-round; processed twice a year as per UGC timeline |

APH routes never use the legacy configurable per-stage day counts: Category 1 shows **As per AICTE Public Notice**, Category 2 shows **Year-round**, and ODL/Online adds the UGC twice-yearly cadence. The handbook does not specify a fixed number of processing days in these table entries.

Scrutiny and EVC steps keep the Clause 1.8/1.9 constraints visible. Deficiency observations are tied to the stage that raised them; institutions attach Compliance Evidence to each deficiency; reviewers preserve every submission, review outcome, timestamp, and audit entry. Evidence upload alone cannot resolve a deficiency or decide an application. Re-Scrutiny is routed only for identified deficiencies. SAC/SHC is not auto-inserted: an authorized NEXORA reviewer must record a reasoned referral after the applicable prior step.

Clause 2.24 eligibility is modelled as one NEXORA appeal entry within seven days of a recorded Executive Committee decision upload. Clause 2.25 decisions must be backed by an uploaded external order/letter and an authority/reference; the API records that external outcome and audits it rather than creating one.

**Prototype boundary:** NEXORA does not connect to the AICTE portal, send applications/compliance/appeals, select AICTE committee members, issue notices, decide eligibility, grant approval, or notify the SAC/SHC/Council. Applicant-supplied course counts, decision references, and uploaded files are not independently verified with AICTE. The implementation is a limited workflow mapping for the cited provisions, not a claim of full APH compliance; other APH clauses, annexures, exceptions, fees, and academic-calendar rules are not comprehensively implemented.

The scheduled monitor also escalates overdue undertakings/compliance submissions and expired documents to configured regional, bureau and administrator roles. In-app alerts are always recorded; when SMTP is configured, new alerts are also emailed to their recipients. Email delivery requires the same `SMTP_HOST` and sender/authentication settings described below.

After the applicant enters an application type, the form suggests an illustrative route from common demo labels (new institution, renewal, expansion, committee, or EVC). The applicant can change the suggestion before submitting. This is a prototype heuristic, not an official APH mapping.

EVC stage deadlines and scheduled visit dates get a reminder when they are within three days and a distinct overdue notification/escalation after they pass. The EVC screen shows overdue stage and visit counts, the dashboard has an **Overdue EVC Actions** KPI, and the EVC CSV includes due date, overdue days and escalation level. Example reminder and escalation intervals remain configurable prototype values—not official AICTE timelines.

```mermaid
flowchart LR
    A[Application submission] --> B[Initial scrutiny]
    B --> C[Deficiency check]
    C --> D[EVC scheduling]
    D --> E[EVC completion]
    E --> F[SAC / SHC / committee]
    F --> G[Authorised decision]
    G --> H[Final application status]
```

## 🎬 Demo accounts & scenarios

The synthetic seed portfolio contains 25 applications across all five regions, with stage histories, varied outcomes and deadlines, EVC visits, review observations, document-validity states and compliance records. Institution names and workflow records are fictional demo data, not official AICTE records.

All seed accounts use the shared demo password:

```text
demo1234
```

| Role | Demo email | Seed scope |
|---|---|---|
| Administrator | `admin@nexora-demo.in` | Workspace administration |
| Regional Officer | `regional@nexora-demo.in` | South region |
| Regional Officer | `north.regional@nexora-demo.in` | North region |
| Regional Officer | `east.regional@nexora-demo.in` | East region |
| Regional Officer | `west.regional@nexora-demo.in` | West region |
| Regional Officer | `central.regional@nexora-demo.in` | Central region |
| Bureau Officer | `bureau@nexora-demo.in` | Workflow and bureau operations |
| EVC / Committee | `evc@nexora-demo.in` | EVC queue |
| Institution | `institution@nexora-demo.in` | Verma Institute of Technology, South |

These are local prototype credentials only. Do not reuse the shared demo password for real accounts or deployments.

### SIH demo run-through
1. Sign in as `institution@nexora-demo.in` and show the institution's scoped application list. Submit a small demo application if you want to show the submission flow.
2. Sign out and sign in as the South regional officer, `regional@nexora-demo.in`. Open an application in the South region, review its timeline, and forward or return it with a clear reason.
3. If you returned an application, sign back in as the owning institution and resubmit it. Then show the updated timeline and notification.
4. For an EVC example without changing the new application through every stage, use the seeded `APP-2026-0003`: demonstrate its EVC scheduling stage as Bureau Officer, then show EVC findings as `evc@nexora-demo.in`.
5. Submit another demo application and try each example route. The selected path is saved on the record and the detail timeline shows only its applicable stages.
6. On the EVC screen, review the overdue-stage and missed-visit indicators; use the dashboard's **Overdue EVC Actions** KPI and export the EVC report to show deadlines and escalation levels.
7. Finish with the dashboard, audit trail and `/aicte-data`. Explain that dashboard workflow records are synthetic demo data and live public data is not connected unless its authorized source is configured.

Before presenting, reset the local demo data if you changed seeded records, confirm the frontend and backend are both running, and practise signing in/out between roles. Do not claim that OCR approves or authenticates documents, or that NEXORA is an official AICTE service.

### Try the end-to-end flows
1. **Submit an application:** Sign in as Institution → Applications → New application → submit. Follow the new record in the application list and detail timeline.
2. **Review a deficiency:** Open `APP-2026-0002` as the institution to resubmit a returned case, or sign in as an authorized officer to return a case with a required reason.
3. **Schedule and complete an EVC:** Sign in as Bureau Officer to schedule `APP-2026-0003`; sign in as EVC / Committee to record findings and a recommendation.
4. **Submit compliance evidence:** Sign in as Institution → Compliance → open or create an undertaking → upload a document and attach it as evidence. An authorized officer can verify it or request a correction.
5. **Review a lease renewal:** Sign in as Institution → Lease Management → open an expired lease and submit renewal evidence where available.
6. **Run an overdue check:** Sign in as Administrator → User Management → Run deadline monitor. Review application, compliance and expired-document escalations, generated notifications and the expanded overdue report.

> [!TIP]
> "Reset demo data" replaces local application records and users with the fictional seed data. Use it only when you are comfortable losing the current local demo records.

## 🐳 Run locally

### Run the complete stack with Docker Compose

Docker Compose starts the production-mode API, PostgreSQL, and frontend behind one web entry point. The database and uploaded documents use persistent Docker volumes. The stack seeds fictional demo records into a fresh database.

1. Copy `.env.production.example` to `.env.production`.
2. Generate independent random values for `POSTGRES_PASSWORD` and `JWT_SECRET` (at least 32 characters for `JWT_SECRET`).
3. Start the stack with `docker compose --env-file .env.production up -d --build`.
4. Open `http://localhost:8080`. Check service status with `docker compose --env-file .env.production ps`; stop with `docker compose --env-file .env.production down`.

For a remote deployment, run the same stack on a server with a persistent Docker host, configure a strong private secret file, set `NEXORA_PORT` and `CORS_ORIGINS` for the public hostname, and put HTTPS/reverse-proxy protection in front of it. Do not expose PostgreSQL directly. This prototype is not certified for real AICTE decisions or sensitive institutional records.

### Requirements
- Python **3.12** recommended for the pinned backend dependency set.
- Node.js and npm.
- PowerShell on Windows (commands below use Windows paths).
- The root `requirements.txt` mirrors `backend/requirements.txt` for Vercel's Python builder; keep both dependency lists in sync.

### 1. Configure and start the backend

From the repository root:

```powershell
python -m venv backend\venv
backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env

$secret = backend\venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
(Get-Content backend\.env) -replace '^JWT_SECRET=.*$', "JWT_SECRET=$secret" |
  Set-Content -Encoding utf8 backend\.env

Set-Location backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API listens at `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs` in development.

### 2. Configure and start the frontend

Open a second PowerShell window at the repository root:

```powershell
Copy-Item frontend\.env.example frontend\.env
Set-Location frontend
npm install
npm run dev
```

Open `http://localhost:5173`. In development, the frontend sends API requests to the same-origin `/api` path and Vite proxies them to `http://127.0.0.1:8000`. This also supports a forwarded development URL without browser cross-origin login failures.

> [!NOTE]
> If port `5173` is already in use, Vite automatically picks the next free port (e.g. `5174`). Use the URL printed in the terminal.

### Registration and first login
Public institution registration creates an **inactive** account that cannot sign in until an administrator activates it in User Management. For a quick local walkthrough, use one of the seeded demo accounts above.

## ⚙️ Configuration

Copy the example files before local development:

- [`backend/.env.example`](./backend/.env.example) — database URL, JWT settings, CORS origins and optional SMTP settings.
- [`frontend/.env.example`](./frontend/.env.example) — optional frontend API base override.

| Setting | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy database connection. Defaults to local SQLite; configure PostgreSQL for shared/production caching (for example `postgresql+psycopg://user:password@host:5432/nexora`). |
| `JWT_SECRET` | Required private signing secret. The backend refuses to start if it is missing or does not meet the minimum-strength checks. |
| `JWT_ALG` | JWT signing algorithm; defaults to `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime; defaults to 480 minutes. |
| `CORS_ORIGINS` | Comma-separated allowed browser origins for the API. |
| `APP_ENV` | Set to `production` to disable interactive API documentation. |
| `FRONTEND_BASE_URL` | Public frontend origin used to build password-reset links (defaults to `http://localhost:5173`). |
| `AI_CHAT_API_KEY` | Optional provider API key for open-ended assistant replies. Set only in `backend/.env`; never expose it in the frontend or commit it. When enabled, chat messages go to the OpenAI-compatible endpoint. |
| `AI_CHAT_MODEL` | Chat model name; defaults to `gpt-4o-mini`. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | SMTP for password recovery and optional email notifications. Password reset requires `SMTP_HOST` and `SMTP_FROM` (or `SMTP_USER`). Port 587 uses STARTTLS; port 465 uses implicit TLS. |
| `AICTE_OGD_API_KEY` | Server-only API key issued by the Open Government Data platform for an authorized public dataset. |
| `AICTE_OGD_RESOURCE_ID` | UUID resource ID for an AICTE dataset whose publisher and access terms have been verified. |
| `AICTE_DATASET_PAGE_URL` | Official dataset information page shown as the source in the dashboard. |
| `AICTE_OGD_PUBLISHER_VERIFIED` | Must be `true` only after verifying the publisher is AICTE and API access is authorized. |
| `AICTE_SYNC_INTERVAL_MINUTES` | Automatic public-data sync interval (5–1440 minutes; defaults to 360). |
| `VITE_API_BASE` | Optional API URL override. Defaults to same-origin `/api`; use an absolute URL only when hosting the API separately. |

The local database and uploaded files are created under `backend/`. Local `.env` files, databases, uploads, virtual environments and frontend build output are excluded from Git.

## 📡 Public AICTE data integration

The `/aicte-data` screen is a dedicated public-data view. It reads only from the backend's public institution cache and displays source attribution, API availability, and last successful synchronization. The backend adapter uses the documented Open Government Data API resource endpoint; it does not call private AICTE portal endpoints, scrape dashboard pages, or infer internal application status.

The Year-wise AICTE Approved Government Engineering Institutes dataset (2019–20 through 2021–22) contains yearly institute and approved-seat totals, not individual institution records. When configured as this source, NEXORA displays those figures as historical aggregates and does not present them as a current or complete AICTE institution list.

No verified AICTE dataset resource ID or public API contract was available during this integration. Therefore the source stays **not configured** by default and the live dashboard intentionally contains no institution rows until a dataset is verified and configured. Obtain the API key and resource ID through the official dataset/API process, then set the server-side variables in `backend/.env`; never put the key in frontend code. The dataset page URL must be an official HTTPS page, and the publisher/access confirmation must be explicitly enabled. The scheduled job syncs immediately on startup and then at the configured interval; an administrator can also request a manual sync.

The cache uses the configured SQLAlchemy database. For shared or production deployments, configure PostgreSQL using the included `psycopg` driver. Local SQLite remains a development-only default. Do not treat cached records as live: the dashboard always shows the last successful synchronization time, and failed syncs preserve the prior cache while marking the source as degraded/unavailable.

AICTE ONOD/Approved Institutions Dashboard access did not provide a documented public API contract during implementation. No undocumented endpoint or authenticated portal data is used. Application tracking, pending stages, EVC schedules, compliance/undertakings and document expiry remain local NEXORA prototype records until AICTE authorizes a data-sharing API for them.

The Approval Process Handbook 2024–2027 is a published policy reference, not a live API. NEXORA's configurable example workflow and reminder rules have not been treated as handbook-derived official rules; do not use them as official compliance requirements.

## 🗂️ Project structure & screens

```text
backend/
  app/
    routers/       Auth, applications, documents, compliance, EVC, reports, admin...
    schemas/       Request and response validation models
    services/      Workflow, audit, notifications, expiry, OCR and scheduling
    config.py      Environment-backed application settings
    deps.py        Authentication, role and record-scope dependencies
  uploads/         Local private document storage (generated at runtime)
  requirements.txt
frontend/
  src/
    api/           API client and download helpers
    auth/          Authentication context
    components/    Shared layout and reusable UI
    pages/         Dashboard and workflow screens
  vite.config.ts   Development server and same-origin API proxy
```

### API domains

All routes are mounted under `/api`. Explore the live, interactive reference at `http://localhost:8000/docs` (development only).

| Router | Prefix | Responsibility |
|---|---|---|
| auth | `/api/auth` | Sign-in, institution registration, forgot/reset password, current session |
| users | `/api/users` | User list, roles, activation, regional assignment |
| admin | `/api/admin` | User management, workflow config, deadline monitor, demo reset |
| applications | `/api/applications` | Application CRUD, stage transitions, observations, search/export |
| documents | `/api/documents` | Upload, review, authenticated downloads, expiry status |
| compliance | `/api/compliance` | Undertakings, evidence, deadlines, verification |
| lease | `/api/lease` | Lease expiry and renewal tracking |
| evc | `/api/evc` | EVC scheduling, committee, findings, recommendations |
| workflow | `/api/workflow` | Configurable example workflow stages/rules and application-type route suggestions (`GET /paths`, `POST /suggest`) |
| workflow | `/api/workflow/aph-rules` | Authenticated APH 2024–2027 rule catalogue used by the prototype |
| dashboard | `/api/dashboard` | Executive KPIs, charts, deadlines, recent work |
| notifications | `/api/notifications` | In-app notifications and read status |
| reports | `/api/reports` | Filtered CSV reports (pendency, EVC queue/visit delays and escalation levels, compliance, etc.) |
| audit | `/api/audit-logs` | Audit history |
| aicte-data | `/api/aicte-data` | Public institution cache, source health, sync |
| assistant | `/api/assistant` | Optional OpenAI-compatible chat replies |
| (root) | `/api/health` | Liveness check |

### Main screens

| Route | Screen |
|---|---|
| `/login`, `/register` | Sign-in and institution access request |
| `/forgot-password`, `/reset-password` | Email-based password recovery (requires SMTP configuration) |
| `/dashboard` | Executive KPIs, charts, deadlines and recent applications |
| `/aicte-data` | Public AICTE institution records, source health and sync freshness |
| `/applications`, `/applications/new`, `/applications/:id` | Search, submit and manage application records |
| `/documents` | Document upload, status and review |
| `/compliance` | Undertakings, deadlines and submitted evidence |
| `/lease` | Lease expiry and renewal tracking |
| `/evc` | EVC visit scheduling and completion |
| `/notifications` | In-app notifications and read status |
| `/reports` | Filtered CSV reports |
| `/users`, `/workflow`, `/audit` | Restricted administration and audit tools |
| `/help` | Roles, safeguards and guided scenarios |

## 🔒 Security and limitations

Security controls are included for this prototype, but they do **not** make it production-certified or ready for real institutional records.

- Passwords are stored as hashes; sessions use signed bearer tokens with a required environment-supplied JWT secret.
- API endpoints enforce authentication, role checks and institution/region/application record scope; inactive users cannot authenticate.
- Public registration is restricted to institution accounts and requires administrator activation before login.
- Login (10/minute), registration (5/hour), password updates (5/hour) and assistant chat (10/minute) have per-IP application-level rate limits. Password-reset requests are limited to 3/hour per normalized email and source IP, with an additional 20/hour per-IP cap. Password recovery sends a single-use link that expires after 30 minutes; links are stored hashed and SMTP must be configured. Multi-worker or production deployments also need shared gateway-level limits.
- A successful password reset invalidates existing bearer sessions for that account; sign in again using the new password.
- Request bodies use validation schemas in the API. File uploads accept PDF/JPG/JPEG/PNG, enforce a 10 MB limit, and use authenticated, authorized download routes.
- Security response headers include content-security policy, clickjacking and MIME-sniffing defenses, referrer and permissions policies; HSTS is sent over HTTPS.
- CSV exports neutralize spreadsheet formula prefixes in data cells.
- Workflow changes and administrative activity are recorded in the audit history. Automated indicators and OCR are advisory only; they do not determine document authenticity or official approval.
- Email is optional. When SMTP is configured, new in-app alerts are also emailed to their recipients; otherwise delivery remains in-app only. SMS and live AICTE system integration are not connected in this prototype.
- SQLite and local file storage are suitable for a local prototype. A real deployment needs an appropriately managed database, private object storage, TLS, backups, monitoring, shared rate limits and deployment-specific security review.
- Set a unique secret in `backend/.env`; never commit credentials or local environment files. If a signing secret may have been exposed, revoke and rotate it.

The requirements and dependency pins were reviewed in prior project work. Re-run dependency vulnerability checks when dependencies change and before any deployment; a past scan is not a guarantee of current safety.

## 🛠️ Useful commands

Run from `frontend/`:

```powershell
npm run dev       # Start the Vite development server
npm run build     # Type-check and create the production frontend bundle
npm run preview   # Serve the production bundle locally
```

Run the backend workflow tests from `backend/`:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests use an isolated in-memory SQLite database and do not modify the demo database.

Run from the repository root:

```powershell
git diff --check
```

---

<div align="center">

**NEXORA AICTE · A fictional approval and compliance workflow prototype**

Designed for clear, accountable, role-aware operations. ⚖️

</div>
