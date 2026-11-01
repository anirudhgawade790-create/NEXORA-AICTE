<div align="center">

# NEXORA AICTE

### Approval & Compliance Intelligence

**A premium, role-aware workflow prototype for institutional approvals, scrutiny and compliance operations.**

<br />

![React](https://img.shields.io/badge/React-18-149ECA?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/status-prototype-52627A)

<br />

**Executive dashboard · Application lifecycle · EVC coordination · Compliance tracking · Auditability**

</div>

> **Prototype notice:** NEXORA is a fictional demonstration project. It is not an official AICTE product, is not connected to AICTE systems, and must not be used to make official regulatory or approval decisions.

---

## Contents

- [What is NEXORA?](#what-is-nexora)
- [What is included](#what-is-included)
- [Roles and access](#roles-and-access)
- [Application workflow](#application-workflow)
- [Demo accounts and scenarios](#demo-accounts-and-scenarios)
- [Run locally](#run-locally)
- [Configuration](#configuration)
- [Project structure](#project-structure)
- [Security and limitations](#security-and-limitations)
- [Useful commands](#useful-commands)

## What is NEXORA?

NEXORA brings the main steps of an institutional approval and compliance journey into one responsive workspace. Institutions can submit applications and supporting evidence; officers can review records and move them through configurable stages; EVC committees can coordinate visits and submit findings; administrators can manage access and prototype workflow settings.

The interface has been redesigned as a polished enterprise SaaS experience with a navy-and-blue visual system, responsive navigation, clear record states, data visualizations, and reusable page styling. The frontend is built around the existing API contracts and role checks. Dashboard metrics and operational records come from the backend rather than presentation-only hardcoded totals.

## What is included

### Workspace and analytics

- Role-aware navigation, collapsible desktop sidebar, mobile drawer, breadcrumbs, global application search, profile menu and notification count.
- Executive dashboard with live application KPIs, status and regional charts, monthly trends, workflow stages, compliance progress, upcoming deadlines and recent applications.
- Application search, filters, sorting, pagination and CSV export.
- Reports for application pendency, regional performance, EVC appointments, compliance, document validity, overdue actions and decisions.

### Application and operations

- Institution application submission and application detail pages.
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
- Help page with role descriptions, safeguards and guided demo scenarios.
- Premium split-screen sign-in and institution access-request screens.

### Visual design and usability

- Responsive layouts for desktop, laptop, tablet and mobile.
- Consistent navy, royal blue, white and soft off-white styling.
- Lucide iconography, Recharts analytics, accessible form labels, visible focus states and reduced-motion support.
- Clear empty, error and loading states across operational pages.

## Roles and access

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

## Application workflow

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

## Demo accounts and scenarios

All five fictional seed accounts use the shared demo password:

```text
demo1234
```

| Role | Demo email | Seed scope |
|---|---|---|
| Administrator | `admin@nexora-demo.in` | Workspace administration |
| Regional Officer | `regional@nexora-demo.in` | South region |
| Bureau Officer | `bureau@nexora-demo.in` | Workflow and bureau operations |
| EVC / Committee | `evc@nexora-demo.in` | EVC queue |
| Institution | `institution@nexora-demo.in` | Verma Institute of Technology, South |

These are local prototype credentials only. Do not reuse the shared demo password for real accounts or deployments.

### Try the end-to-end flows

1. **Submit an application:** Sign in as Institution → Applications → New application → submit. Follow the new record in the application list and detail timeline.
2. **Review a deficiency:** Open `APP-2026-0002` as the institution to resubmit a returned case, or sign in as an authorized officer to return a case with a required reason.
3. **Schedule and complete an EVC:** Sign in as Bureau Officer to schedule `APP-2026-0003`; sign in as EVC / Committee to record findings and a recommendation.
4. **Submit compliance evidence:** Sign in as Institution → Compliance → open or create an undertaking → upload a document and attach it as evidence. An authorized officer can verify it or request a correction.
5. **Review a lease renewal:** Sign in as Institution → Lease Management → open an expired lease and submit renewal evidence where available.
6. **Run an overdue check:** Sign in as Administrator → User Management → Run deadline monitor. Review resulting notifications and overdue records.

> **Destructive action:** “Reset demo data” replaces local application records and users with the fictional seed data. Use it only when you are comfortable losing the current local demo records.

## Run locally

### Requirements

- Python **3.12** recommended for the pinned backend dependency set.
- Node.js and npm.
- PowerShell on Windows (commands below use Windows paths).

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

### Registration and first login

Public institution registration creates an **inactive** account that cannot sign in until an administrator activates it in User Management. For a quick local walkthrough, use one of the seeded demo accounts above.

## Configuration

Copy the example files before local development:

- [`backend/.env.example`](./backend/.env.example) — database URL, JWT settings, CORS origins and optional SMTP settings.
- [`frontend/.env.example`](./frontend/.env.example) — optional frontend API base override.

| Setting | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy database connection. Defaults to local SQLite. |
| `JWT_SECRET` | Required private signing secret. The backend refuses to start if it is missing or does not meet the minimum-strength checks. |
| `JWT_ALG` | JWT signing algorithm; defaults to `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime; defaults to 480 minutes. |
| `CORS_ORIGINS` | Comma-separated allowed browser origins for the API. |
| `APP_ENV` | Set to `production` to disable interactive API documentation. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Optional email delivery configuration. Without SMTP, notifications remain in-app. |
| `VITE_API_BASE` | Optional API URL override. Defaults to same-origin `/api`; use an absolute URL only when hosting the API separately. |

The local database and uploaded files are created under `backend/`. Local `.env` files, databases, uploads, virtual environments and frontend build output are excluded from Git.

## Project structure

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

### Main screens

| Route | Screen |
|---|---|
| `/login`, `/register` | Sign-in and institution access request |
| `/dashboard` | Executive KPIs, charts, deadlines and recent applications |
| `/applications`, `/applications/new`, `/applications/:id` | Search, submit and manage application records |
| `/documents` | Document upload, status and review |
| `/compliance` | Undertakings, deadlines and submitted evidence |
| `/lease` | Lease expiry and renewal tracking |
| `/evc` | EVC visit scheduling and completion |
| `/notifications` | In-app notifications and read status |
| `/reports` | Filtered CSV reports |
| `/users`, `/workflow`, `/audit` | Restricted administration and audit tools |
| `/help` | Roles, safeguards and guided scenarios |

## Security and limitations

Security controls are included for this prototype, but they do **not** make it production-certified or ready for real institutional records.

- Passwords are stored as hashes; sessions use signed bearer tokens with a required environment-supplied JWT secret.
- API endpoints enforce authentication, role checks and institution/region/application record scope; inactive users cannot authenticate.
- Public registration is restricted to institution accounts and requires administrator activation before login.
- Login and registration have per-IP application-level rate limits. Multi-worker or production deployments also need shared gateway-level limits.
- Request bodies use validation schemas in the API. File uploads accept PDF/JPG/JPEG/PNG, enforce a 10 MB limit, and use authenticated, authorized download routes.
- Security response headers include content-security policy, clickjacking and MIME-sniffing defenses, referrer and permissions policies; HSTS is sent over HTTPS.
- CSV exports neutralize spreadsheet formula prefixes in data cells.
- Workflow changes and administrative activity are recorded in the audit history. Automated indicators and OCR are advisory only; they do not determine document authenticity or official approval.
- Email is optional. When SMTP is not configured, the application explicitly reports in-app-only delivery.
- SQLite and local file storage are suitable for a local prototype. A real deployment needs an appropriately managed database, private object storage, TLS, backups, monitoring, shared rate limits and deployment-specific security review.
- Set a unique secret in `backend/.env`; never commit credentials or local environment files. If a signing secret may have been exposed, revoke and rotate it.

The requirements and dependency pins were reviewed in prior project work. Re-run dependency vulnerability checks when dependencies change and before any deployment; a past scan is not a guarantee of current safety.

## Useful commands

Run from `frontend/`:

```powershell
npm run dev       # Start the Vite development server
npm run build     # Type-check and create the production frontend bundle
npm run preview   # Serve the production bundle locally
```

Run from the repository root:

```powershell
git diff --check
```

---

<div align="center">

**NEXORA AICTE · A fictional approval and compliance workflow prototype**

Designed for clear, accountable, role-aware operations.

</div>
